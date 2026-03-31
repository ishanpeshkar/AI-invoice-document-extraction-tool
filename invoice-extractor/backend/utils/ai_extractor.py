import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EXTRACTION_PROMPT = """
You are an expert invoice and document data extraction system.

LANGUAGE: The document may be in ANY language (Hindi, Arabic, Chinese, English, etc.). Extract all fields regardless of language. Return field values exactly as they appear in the document.

HANDWRITING: The document may contain handwritten, printed, or scanned text. Extract all readable content.

CRITICAL VENDOR RULE:
- The VENDOR is the company that ISSUED or SENT this invoice — the seller or service provider.
- They appear in the "From:", "Issued by:", "Seller:", or the header/logo section at the top.
- The "To:", "Bill To:", "Buyer:", or "Ship To:" field is the CUSTOMER — do NOT extract this as the vendor.
- The vendor is whoever is RECEIVING the payment.

Return ONLY a valid JSON object. No explanation, no markdown, no extra text — just raw JSON.

{
  "vendor_name": "string or null",
  "gstin": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "string or null",
  "pan_number": "string or null",
  "payment_terms": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": "string",
      "rate": "string",
      "amount": "string"
    }
  ],
  "subtotal": "string or null",
  "cgst": "string or null",
  "sgst": "string or null",
  "igst": "string or null",
  "total_amount": "string or null"
}

Rules:
- Use null for any field not present
- Keep all numeric values as strings — preserve original formatting
- Extract ALL line items
- Preserve original date format
"""


def _parse_response(raw_text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        raw_text = parts[1] if len(parts) > 1 else raw_text
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return json.loads(raw_text.strip())


def extract_from_images(base64_images: list[str]) -> dict:
    """Send base64 images to Groq vision model."""
    image_content = []
    for b64 in base64_images:
        image_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"}
        })
    image_content.append({"type": "text", "text": EXTRACTION_PROMPT})

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": image_content}],
        temperature=0,
        max_tokens=2000,
    )
    return _parse_response(response.choices[0].message.content)


def extract_from_text(text: str) -> dict:
    """Send raw text to Groq LLM."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"{EXTRACTION_PROMPT}\n\nDocument text:\n{text}"
        }],
        temperature=0,
        max_tokens=2000,
    )
    return _parse_response(response.choices[0].message.content)


def merge_extractions(results: list[dict]) -> dict:
    """
    Merge extractions from multiple page chunks.
    - Header fields (vendor, GSTIN etc.) taken from first non-null occurrence
    - Line items merged from all pages
    - Total taken from last chunk (usually on last page)
    """
    if not results:
        return {}
    if len(results) == 1:
        return results[0]

    header_fields = ["vendor_name", "gstin", "invoice_number",
                     "invoice_date", "pan_number", "payment_terms"]
    total_fields = ["subtotal", "cgst", "sgst", "igst", "total_amount"]

    merged = {field: None for field in header_fields + total_fields}
    merged["line_items"] = []

    # Header fields — first non-null wins
    for field in header_fields:
        for result in results:
            if result.get(field):
                merged[field] = result[field]
                break

    # Line items — collect from all pages
    for result in results:
        items = result.get("line_items") or []
        merged["line_items"].extend(items)

    # Total fields — last non-null wins (totals are usually on last page)
    for field in total_fields:
        for result in reversed(results):
            if result.get(field):
                merged[field] = result[field]
                break

    return merged


def extract_multipage(image_chunks: list[list[str]]) -> dict:
    """Process multipage document in chunks and merge results."""
    results = []
    for chunk in image_chunks:
        try:
            result = extract_from_images(chunk)
            results.append(result)
        except Exception as e:
            print(f"[WARNING] Chunk extraction failed: {e}")
            continue

    return merge_extractions(results)
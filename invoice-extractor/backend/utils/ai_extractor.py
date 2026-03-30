import os
import json
import base64
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EXTRACTION_PROMPT = """
You are an expert invoice data extraction system. The document may be in any language - extract all fields regardless of language and return values exactly as they appear.

The document may contain handwritten, printed, or scanned text. Extract all readable fields.

CRITICAL VENDOR RULE:
- The VENDOR is the company that ISSUED/SENT the invoice - the seller or service provider. They appear in the "From:", "Issued by:", or header/logo section.
- The "To:", "Bill To:", or "Buyer" field is the CUSTOMER - do NOT extract this as the vendor.
- If unclear, the vendor is whoever is receiving the payment.

Return ONLY a valid JSON object. No explanation, no markdown, no extra text.

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
- Use null for any field not found
- Keep all numeric values as strings
- Extract ALL line items found
- Preserve original date format
- If the document has multiple pages, extract data from all pages and merge line items
"""


def extract_from_images(base64_images: list[str]) -> dict:
    """Send base64 images to Groq vision model and extract invoice data."""

    # Build image content blocks (use first 3 pages max to stay within limits)
    image_content = []
    for b64 in base64_images[:10]:
        image_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}"
            }
        })

    image_content.append({
        "type": "text",
        "text": EXTRACTION_PROMPT
    })

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": image_content
            }
        ],
        temperature=0,
        max_tokens=2000,
    )

    raw_text = response.choices[0].message.content.strip()

    # Clean up any accidental markdown code fences
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    return json.loads(raw_text)


def extract_from_text(text: str) -> dict:
    """Send raw text to Groq LLM and extract invoice data."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nInvoice text:\n{text}"
            }
        ],
        temperature=0,
        max_tokens=2000,
    )

    raw_text = response.choices[0].message.content.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    return json.loads(raw_text)
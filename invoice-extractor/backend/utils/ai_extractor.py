import os
import json
import base64
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EXTRACTION_PROMPT = """
You are an expert invoice data extraction system.
Extract all available fields from this invoice document and return ONLY a valid JSON object.
Do not include any explanation, markdown, or extra text — just the raw JSON.

Required JSON structure:
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
- Use null for any field not found in the document
- Keep all numeric values as strings (preserve original formatting)
- Extract ALL line items found
- For invoice_date, preserve the original format from the document
"""


def extract_from_images(base64_images: list[str]) -> dict:
    """Send base64 images to Groq vision model and extract invoice data."""

    # Build image content blocks (use first 3 pages max to stay within limits)
    image_content = []
    for b64 in base64_images[:3]:
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
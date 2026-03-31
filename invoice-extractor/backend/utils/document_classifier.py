import fitz
import io
from PIL import Image
import numpy as np

def classify_document(file_bytes: bytes, content_type: str) -> dict:
    """
    Detects document type and returns routing decision.
    Returns:
    {
        "doc_type": "digital_pdf" | "scanned_pdf" | "image" | "handwritten_image" | "docx" | "text",
        "route_to": "ai_vision" | "ocr" | "text_llm",
        "page_count": int,
        "confidence": "high" | "medium" | "low",
        "notes": str
    }
    """

    if content_type in ("application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        return {
            "doc_type": "docx",
            "route_to": "text_llm",
            "page_count": 1,
            "confidence": "high",
            "notes": "Word document — extracting text directly"
        }

    if content_type == "application/pdf":
        return _classify_pdf(file_bytes)

    if content_type in ("image/jpeg", "image/jpg", "image/png"):
        return _classify_image(file_bytes)

    return {
        "doc_type": "unknown",
        "route_to": "ai_vision",
        "page_count": 1,
        "confidence": "low",
        "notes": "Unknown type — attempting AI vision"
    }


def _classify_pdf(file_bytes: bytes) -> dict:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    total_text = ""

    for page in doc:
        total_text += page.get_text().strip()

    doc.close()

    # If substantial text exists — it's a digital/searchable PDF
    if len(total_text) > 100:
        return {
            "doc_type": "digital_pdf",
            "route_to": "ai_vision",
            "page_count": page_count,
            "confidence": "high",
            "notes": f"Digital PDF with extractable text — {page_count} page(s)"
        }
    else:
        # No text layer — it's a scanned PDF (image-based)
        return {
            "doc_type": "scanned_pdf",
            "route_to": "ai_vision",
            "page_count": page_count,
            "confidence": "medium",
            "notes": f"Scanned PDF — no text layer detected — {page_count} page(s) — using vision model"
        }


def _classify_image(file_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    width, height = image.size

    # Check image quality
    img_array = np.array(image.convert("L"))
    contrast = float(img_array.std())

    if contrast < 30:
        return {
            "doc_type": "handwritten_image",
            "route_to": "ai_vision",
            "page_count": 1,
            "confidence": "low",
            "notes": f"Low contrast image ({contrast:.1f}) — possibly handwritten or poor scan — results may be inaccurate"
        }
    elif width < 800 or height < 800:
        return {
            "doc_type": "image",
            "route_to": "ai_vision",
            "page_count": 1,
            "confidence": "medium",
            "notes": f"Low resolution image ({width}x{height}) — will upscale before extraction"
        }
    else:
        return {
            "doc_type": "image",
            "route_to": "ai_vision",
            "page_count": 1,
            "confidence": "high",
            "notes": f"Good quality image ({width}x{height})"
        }
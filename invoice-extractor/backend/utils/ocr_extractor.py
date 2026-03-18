import os
import io
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from utils.ai_extractor import extract_from_text

# Lazy load easyocr to avoid slow startup
_reader = None

def get_ocr_reader():
    """Lazy-load EasyOCR reader on first use."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def pdf_to_images(file_bytes: bytes) -> list:
    """Convert PDF pages to PIL images."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def image_bytes_to_pil(file_bytes: bytes) -> Image.Image:
    """Convert raw image bytes to PIL image."""
    return Image.open(io.BytesIO(file_bytes)).convert("RGB")


def run_ocr_on_image(pil_image: Image.Image) -> str:
    """Run EasyOCR on a PIL image and return extracted text."""
    reader = get_ocr_reader()
    img_array = np.array(pil_image)
    results = reader.readtext(img_array, detail=0, paragraph=True)
    return "\n".join(results)


def extract_via_ocr(file_bytes: bytes, content_type: str) -> dict:
    """
    Full OCR pipeline:
    1. Convert file to images
    2. Run EasyOCR on each page
    3. Combine raw text
    4. Pass to LLM for structured extraction
    """
    raw_text_pages = []

    if content_type == "application/pdf":
        images = pdf_to_images(file_bytes)
        for img in images[:3]:  # limit to first 3 pages
            text = run_ocr_on_image(img)
            raw_text_pages.append(text)

    elif content_type in ("image/jpeg", "image/jpg", "image/png"):
        pil_image = image_bytes_to_pil(file_bytes)
        text = run_ocr_on_image(pil_image)
        raw_text_pages.append(text)

    else:
        raise ValueError(f"OCR not supported for file type: {content_type}")

    combined_text = "\n\n".join(raw_text_pages)

    # Pass OCR text to LLM for structured extraction
    extracted = extract_from_text(combined_text)
    extracted["_ocr_raw_text"] = combined_text  # store raw OCR output for debugging

    return extracted
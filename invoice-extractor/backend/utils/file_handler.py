import fitz  # PyMuPDF
import base64
import io
from docx import Document
from PIL import Image

SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "application/msword": "docx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def get_file_type(content_type: str) -> str:
    return SUPPORTED_TYPES.get(content_type, "unknown")


def pdf_to_base64_images(file_bytes: bytes) -> list[str]:
    """Convert each page of a PDF to a base64 image string."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(b64)
    return images


def image_to_base64(file_bytes: bytes, content_type: str) -> str:
    """Convert image to base64 with preprocessing for better AI extraction."""
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    # Upscale small images - vision models work better on larger images
    width, height = image.size
    if width < 1000 or height < 1000:
        scale = max(1000 / width, 1000 / height)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # Enhance contrast and sharpness for better text visibility
    from PIL import ImageEnhance

    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = ImageEnhance.Sharpness(image).enhance(2.0)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def docx_to_text(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def prepare_file_for_extraction(file_bytes: bytes, content_type: str) -> dict:
    """
    Returns a dict with:
    - type: 'images' | 'text'
    - data: list of base64 strings (for images/pdf) OR raw text string (for docx/text)
    """
    file_type = get_file_type(content_type)

    if file_type == "pdf":
        images = pdf_to_base64_images(file_bytes)
        return {"type": "images", "data": images}

    elif file_type == "image":
        b64 = image_to_base64(file_bytes, content_type)
        return {"type": "images", "data": [b64]}

    elif file_type == "docx":
        text = docx_to_text(file_bytes)
        return {"type": "text", "data": text}

    else:
        raise ValueError(f"Unsupported file type: {content_type}")
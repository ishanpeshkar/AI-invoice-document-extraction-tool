import fitz
import base64
import io
from docx import Document
from PIL import Image, ImageEnhance

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


def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhance image quality for better AI extraction."""
    image = image.convert("RGB")

    # Upscale small images
    width, height = image.size
    if width < 1500 or height < 1500:
        scale = max(1500 / width, 1500 / height)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # Enhance contrast and sharpness
    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = ImageEnhance.Sharpness(image).enhance(2.5)
    image = ImageEnhance.Brightness(image).enhance(1.1)

    return image


def image_to_base64(pil_image: Image.Image) -> str:
    """Convert PIL image to base64 PNG string."""
    buffer = io.BytesIO()
    pil_image.convert("RGB").save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pdf_to_page_images(file_bytes: bytes) -> list[Image.Image]:
    """Convert each PDF page to a PIL image."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=250)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images


def pdf_to_base64_images(file_bytes: bytes) -> list[str]:
    """Convert PDF pages to preprocessed base64 images."""
    page_images = pdf_to_page_images(file_bytes)
    result = []
    for img in page_images:
        processed = preprocess_image(img)
        result.append(image_to_base64(processed))
    return result


def split_pdf_into_chunks(file_bytes: bytes, chunk_size: int = 3) -> list[list[str]]:
    """Split PDF pages into chunks of base64 images for multipage processing."""
    all_images = pdf_to_base64_images(file_bytes)
    chunks = []
    for i in range(0, len(all_images), chunk_size):
        chunks.append(all_images[i:i + chunk_size])
    return chunks


def docx_to_text(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def prepare_file_for_extraction(file_bytes: bytes, content_type: str) -> dict:
    """
    Returns unified extraction input.
    For multipage PDFs returns multiple chunks.
    """
    file_type = get_file_type(content_type)

    if file_type == "pdf":
        chunks = split_pdf_into_chunks(file_bytes, chunk_size=3)
        return {
            "type": "image_chunks",
            "data": chunks,
            "page_count": sum(len(c) for c in chunks)
        }

    elif file_type == "image":
        img = Image.open(io.BytesIO(file_bytes))
        processed = preprocess_image(img)
        b64 = image_to_base64(processed)
        return {"type": "images", "data": [b64], "page_count": 1}

    elif file_type == "docx":
        text = docx_to_text(file_bytes)
        return {"type": "text", "data": text, "page_count": 1}

    else:
        raise ValueError(f"Unsupported file type: {content_type}")
import io
import fitz  # PyMuPDF
from PIL import Image as PILImage


def extract(pdf_bytes: bytes, source_label: str) -> tuple[str, list[dict]]:
    """
    Extract text and images from a PDF.
    Returns (text, images) where images is a list of dicts:
      { data: bytes, source: str, page: int, index: int }
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    images = []

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages_text.append(f"[Page {page_num + 1}]\n{text}")

        for img_idx, img_ref in enumerate(page.get_images(full=True)):
            xref = img_ref[0]
            raw = doc.extract_image(xref)
            try:
                pil = PILImage.open(io.BytesIO(raw["image"])).convert("RGB")
                buf = io.BytesIO()
                pil.save(buf, "JPEG", quality=85)
                images.append({
                    "data":   buf.getvalue(),
                    "source": source_label,
                    "page":   page_num + 1,
                    "index":  img_idx,
                })
            except Exception:
                pass

    doc.close()
    return "\n\n".join(pages_text), images

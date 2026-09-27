from pathlib import Path

def extract_pdf(path: str) -> list[tuple[int, str]]:
    """Extract text; use OCR only for pages with no extractable text."""
    try:
        import fitz
        doc = fitz.open(path)
        pages = []
        for number, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            # Image-only pages usually return little or no text from PyMuPDF.
            if len(text) < 20:
                text = ocr_page(page)
            pages.append((number, text))
        return pages
    except Exception:
        return []

def ocr_page(page) -> str:
    try:
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(matrix=__import__("fitz").Matrix(2, 2))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(image)
    except Exception:
        return "[OCR unavailable: install tesseract and pytesseract]"

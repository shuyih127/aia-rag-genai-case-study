import hashlib
import re

def language(text: str) -> str:
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    return "zh" if cn > en else "en"

def make_id(document: str, page: int, index: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"{document.replace(' ', '_')}_page_{page}_chunk_{index:02d}_{digest}"

def chunk_text(text: str, document: str, page: int = 1, size: int = 650, overlap: int = 80):
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start = [], 0
    index = 1
    # Overlap preserves context when a fact falls across two chunk boundaries.
    while start < len(text):
        end = min(len(text), start + size)
        piece = text[start:end]
        chunks.append({"id": make_id(document, page, index, piece), "text": piece, "document": document, "page": page, "language": language(piece), "section": "document"})
        if end == len(text): break
        start = max(start + 1, end - overlap)
        index += 1
    return chunks

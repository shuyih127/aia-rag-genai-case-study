from pathlib import Path
import json
from .chunking import chunk_text
from .ocr import extract_pdf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "chunks.jsonl"

def ingest():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chunks = []
    # This is a batch preprocessing job. The serving API reads the processed
    # index later; it does not re-ingest every document for every user question.
    for path in sorted(RAW.glob("*.txt")):
        for page, text in [(1, path.read_text(encoding="utf-8"))]:
            chunks.extend(chunk_text(text, path.name, page))
    for path in sorted(RAW.glob("*.pdf")):
        for page, text in extract_pdf(str(path)):
            chunks.extend(chunk_text(text, path.name, page))
    # JSONL keeps one independently inspectable metadata-rich chunk per line.
    OUT.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in chunks) + "\n", encoding="utf-8")
    print(f"Indexed {len(chunks)} chunks to {OUT}")

if __name__ == "__main__":
    ingest()

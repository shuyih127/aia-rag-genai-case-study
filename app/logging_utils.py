import hashlib
import json
import os
import time
from datetime import datetime, timezone
from .config import settings

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def write_event(event: dict) -> None:
    os.makedirs(settings.log_dir, exist_ok=True)
    with open(os.path.join(settings.log_dir, "requests.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def cost_for_tokens(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * settings.input_price_per_million + (output_tokens / 1_000_000) * settings.output_price_per_million

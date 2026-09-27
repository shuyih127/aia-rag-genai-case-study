from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load local configuration without hard-coding secrets or environment-specific values.
load_dotenv()

def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    # Claude is optional: an empty key keeps the demo runnable in local fallback mode.
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    reranker_model: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    # Embeddings and reranking are independent retrieval upgrades, not requirements
    # for the deterministic keyword-search fallback.
    embedding_enabled: bool = _bool("EMBEDDING_ENABLED")
    reranker_enabled: bool = _bool("RERANKER_ENABLED")
    top_k: int = int(os.getenv("TOP_K", "5"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.0"))
    prompt_cache_enabled: bool = _bool("PROMPT_CACHE_ENABLED")
    low_confidence_threshold: float = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.10"))
    data_dir: str = os.getenv("DATA_DIR", "data")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    input_price_per_million: float = float(os.getenv("INPUT_PRICE_PER_MILLION", "3.0"))
    output_price_per_million: float = float(os.getenv("OUTPUT_PRICE_PER_MILLION", "15.0"))

settings = Settings()

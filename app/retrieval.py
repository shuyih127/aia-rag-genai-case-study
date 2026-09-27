from dataclasses import dataclass
from pathlib import Path
import json
import math
import re
import time
from .config import settings

@dataclass
class Chunk:
    id: str
    text: str
    document: str
    page: int | None
    language: str
    section: str
    score: float = 0.0

class Retriever:
    def __init__(self, index_path: str | None = None):
        self.index_path = Path(index_path or settings.data_dir) / "processed" / "chunks.jsonl"
        self.chunks: list[Chunk] = []
        self._model = None
        self._vectors = None
        self.load()

    def load(self) -> None:
        if not self.index_path.exists():
            return
        self.chunks = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                self.chunks.append(Chunk(**item))
        # Load optional multilingual embeddings once at service startup so each
        # request can reuse the index rather than recomputing document vectors.
        if settings.embedding_enabled:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(settings.embedding_model)
                self._vectors = self._model.encode([c.text for c in self.chunks], normalize_embeddings=True)
            except Exception:
                self._model = None

    @staticmethod
    def _tokens(text: str) -> set[str]:
        words = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
        stopwords = {"what", "is", "the", "a", "an", "of", "to", "for", "how", "many", "must", "i", "submit", "request", "where", "who", "does", "and", "or", "in", "on", "it", "this", "that"}
        return {word for word in words if word not in stopwords}

    def _lexical_score(self, query: str, text: str) -> float:
        q, d = self._tokens(query), self._tokens(text)
        if not q or not d:
            return 0.0
        # This deterministic overlap score is the no-credential fallback.
        overlap = len(q & d) / len(q)
        return min(1.0, overlap + (0.15 if query.lower() in text.lower() else 0.0))

    def search(self, query: str, top_k: int | None = None, mode: str = "hybrid", rerank: bool | None = None) -> tuple[list[Chunk], float, float]:
        started = time.perf_counter()
        top_k = top_k or settings.top_k
        if not self.chunks:
            return [], 0.0, 0.0
        lexical = [self._lexical_score(query, c.text) for c in self.chunks]
        semantic = [0.0] * len(self.chunks)
        # Query embeddings are computed only when the optional local embedding
        # model loaded successfully; otherwise lexical search remains available.
        if self._model is not None:
            try:
                qv = self._model.encode([query], normalize_embeddings=True)[0]
                semantic = [float(v) for v in self._vectors @ qv]
            except Exception:
                pass
        scores = []
        for i, c in enumerate(self.chunks):
            if mode == "vector" and self._model is not None:
                score = semantic[i]
            elif mode == "keyword":
                score = lexical[i]
            else:
                # Hybrid remains useful in fallback mode and rewards exact lexical hits.
                score = 0.65 * semantic[i] + 0.35 * lexical[i] if self._model is not None else lexical[i]
            scores.append(score)
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[: max(top_k, 8)]:
            c = self.chunks[i]
            c.score = scores[i]
            results.append(c)
        # Avoid silently downloading a large model during tests when reranking
        # is not explicitly enabled in the environment.
        use_reranker = settings.reranker_enabled and (rerank is not False)
        if use_reranker and results:
            try:
                from sentence_transformers import CrossEncoder
                ranker = CrossEncoder(settings.reranker_model)
                pairs = [(query, c.text) for c in results]
                rr = ranker.predict(pairs)
                results = [c for _, c in sorted(zip(rr, results), key=lambda x: x[0], reverse=True)]
            except Exception:
                pass
        results = results[:top_k]
        elapsed = (time.perf_counter() - started) * 1000
        return results, (results[0].score if results else 0.0), elapsed

retriever = Retriever()

"""Run a lightweight retrieval/cost sensitivity analysis without model calls."""
import json
from pathlib import Path
from app.retrieval import Retriever
from app.config import settings

ROOT = Path(__file__).resolve().parents[1]

def main():
    retriever = Retriever()
    questions = [json.loads(x) for x in (ROOT / "evals/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = []
    for top_k in (3, 5, 8):
        for reranker in (False, True):
            for temperature in (0.0, 0.3, 0.7):
                for mode in ("vector", "hybrid"):
                    scores = []
                    for q in questions:
                        hits, score, _ = retriever.search(q["question"], top_k=top_k, mode=mode, rerank=reranker)
                        if q["answerable"]:
                            scores.append(1 if hits and any(g in hits[0].document for g in q["gold_source_ids"]) else 0)
                        else:
                            scores.append(1 if not hits or score < settings.low_confidence_threshold else 0)
                    # Conservative interview estimate: 900 input and 180 output tokens per call.
                    per_1000 = (900 * settings.input_price_per_million + 180 * settings.output_price_per_million) / 1_000
                    rows.append({"top_k": top_k, "reranker": reranker, "temperature": temperature, "mode": mode, "retrieval_success": sum(scores) / len(scores), "estimated_cost_per_1000_usd": round(per_1000, 6)})
    out = ROOT / "evals" / "results" / "sensitivity.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} configurations to {out}")

if __name__ == "__main__":
    main()

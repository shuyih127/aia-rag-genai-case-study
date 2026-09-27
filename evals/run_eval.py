import json
import time
from pathlib import Path
import httpx
from .metrics import citation_validity, context_precision, faithfulness, percentile

ROOT = Path(__file__).resolve().parents[1]

def run():
    questions = [json.loads(x) for x in (ROOT / "evals/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    results, latencies = [], []
    # Use an in-process ASGI client so the evaluation works in restricted
    # environments where binding a local TCP port is unavailable.
    from fastapi.testclient import TestClient
    from app.api import app
    client = TestClient(app)
    with client:
        for item in questions:
            start = time.perf_counter()
            try:
                data = client.post("/chat", json={"question": item["question"], "language": item["language"]}).json()
                elapsed = (time.perf_counter() - start) * 1000
            except Exception as exc:
                data, elapsed = {"answer": f"error: {exc}", "refused": True, "citations": []}, 0
            latencies.append(elapsed)
            retrieved = [c.get("document", "") for c in data.get("citations", [])]
            contexts = [c.get("snippet", "") for c in data.get("citations", [])]
            expected_refusal = not item["answerable"]
            refusal_ok = bool(data.get("refused")) == expected_refusal
            # The refusal/answerability proxy is deliberately reported separately
            # from semantic answer accuracy, which needs human-reviewed references.
            results.append({"id": item["id"], "answer": data.get("answer", ""), "refused": data.get("refused", False), "refusal_correct": refusal_ok, "citation_validity": citation_validity(data.get("answer", ""), len(data.get("citations", []))), "context_precision": context_precision(retrieved, item["gold_source_ids"]), "faithfulness": faithfulness(data.get("answer", ""), contexts), "latency_ms": elapsed})
    summary = {"count": len(results), "accuracy_proxy": sum(r["refusal_correct"] for r in results) / len(results), "faithfulness": sum(r["faithfulness"] for r in results) / len(results), "context_precision": sum(r["context_precision"] for r in results) / len(results), "citation_validity": sum(r["citation_validity"] for r in results) / len(results), "p50_ms": percentile(latencies, 50), "p95_ms": percentile(latencies, 95), "results": results}
    output = ROOT / "evals" / "results"
    output.mkdir(exist_ok=True)
    (output / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))

if __name__ == "__main__":
    run()

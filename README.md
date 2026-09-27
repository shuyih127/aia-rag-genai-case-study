# RAG + Generative AI Service

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m ingest.ingest_documents
uvicorn app.api:app --reload
streamlit run ui/streamlit_app.py
```

The demo works without a Claude key or downloaded embedding model by using a deterministic lexical fallback. Set `ANTHROPIC_API_KEY` for Claude generation and `EMBEDDING_MODEL` for multilingual embeddings.

## Knowledge-base data disclosure

The real internal AIA knowledge base was not provided for this assessment. The files in `data/raw/` are synthetic demonstration documents written with GPT to reproduce the required document categories and bilingual/scanned-PDF behavior. 

The scanned PDF is also a generated test fixture. It exists to verify that the OCR branch can process an image-only PDF.

## VS Code workflow

Open this folder in VS Code, select `.venv` as the Python interpreter, run the `ingest` module once, then start the API and Streamlit terminals. The REST API is available at `http://localhost:8000/docs`.

## Architecture

`raw documents -> extraction/OCR -> metadata chunks -> hybrid retrieval -> optional reranking -> grounded Claude answer -> citation validation -> redacted JSON log`

Retrieved content is treated as untrusted context. The generator is not given shell, network, write, or database tools. Low-confidence retrieval returns a refusal rather than an unsupported answer.

## Evaluation

```bash
python -m evals.run_eval
```

This runs the included 40-question set, reports accuracy, citation validity, refusal correctness, faithfulness, context precision, latency, and cost estimates, and writes JSON output under `evals/results/`.

The evaluation harness is intentionally transparent: the default faithfulness score is a claim-level deterministic rubric suitable for a local MVP; when Claude is configured, the same harness can use Claude as an evaluator.

Each real API or evaluation request writes a structured event to `logs/requests.jsonl`. That file is generated at runtime and is intentionally excluded from the submitted source tree because it may contain operational metadata. A sanitized illustrative log is kept separately in `sample_logs/sample_log.json` for the required PII-redacted sample-log deliverable.

## Configuration

See `.env.example`. Important settings include `TOP_K`, `RERANKER_ENABLED`, `TEMPERATURE`, `LOW_CONFIDENCE_THRESHOLD`, `EMBEDDING_MODEL`, and the Claude model name. Prices are configurable so the cost report can be rerun with the pricing available on the evaluation date.

## What I Will Do In a Production Environment

A production deployment would add authenticated access control, a managed index, encrypted storage, secret management, retention policies, and independent security review.

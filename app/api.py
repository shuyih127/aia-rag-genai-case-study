import time
import uuid
from fastapi import FastAPI
from .conversation import Turn, get_session, standalone_query
from .config import settings
from .generation import generator, valid_citations
from .logging_utils import cost_for_tokens, hash_text, now_iso, write_event
from .models import ChatRequest, ChatResponse, Citation, SessionResponse
from .retrieval import retriever
from .security import injection_suspected, redact_pii

app = FastAPI(title="AIA Bilingual RAG QA", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(retriever.chunks), "claude_enabled": generator.client is not None}

@app.post("/sessions", response_model=SessionResponse)
def create_session():
    return SessionResponse(session_id=get_session(None).id)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    session = get_session(request.session_id)
    # Request flow: security screening -> session/query handling -> retrieval
    # -> confidence gate -> generation -> citation validation -> logging.
    query = standalone_query(request.question, session)
    if injection_suspected(request.question):
        answer = "I can’t help reveal system instructions or personal data. I can answer questions supported by the internal knowledge base."
        write_event({"request_id": request_id, "session_id": session.id, "timestamp": now_iso(), "query_hash": hash_text(request.question), "retrieved_source_ids": [], "refusal": True, "injection_suspected": True, "total_ms": (time.perf_counter()-started)*1000, "error": None})
        return ChatResponse(answer=answer, refused=True, request_id=request_id)
    chunks, top_score, retrieval_ms = retriever.search(query)
    # Refuse rather than ask the generator to guess when retrieval is empty or weak.
    refused = not chunks or top_score < settings.low_confidence_threshold
    citations = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    if refused:
        answer = "I couldn’t find sufficiently relevant information in the knowledge base to answer that question."
    else:
        answer, usage = generator.answer(request.question, chunks, session.turns)
        # Only citations that point to returned chunks are exposed to the user.
        valid = valid_citations(answer, len(chunks))
        citations = [Citation(id=f"S{i}", document=chunks[i-1].document, page=chunks[i-1].page, snippet=redact_pii(chunks[i-1].text[:300])) for i in valid]
        if not valid:
            answer = "I found relevant material, but could not produce a verifiable citation-backed answer."
            refused = True
    session.turns.append(Turn(request.question, answer))
    total_ms = (time.perf_counter() - started) * 1000
    write_event({"request_id": request_id, "session_id": session.id, "timestamp": now_iso(), "language": request.language, "query_hash": hash_text(request.question), "rewritten_query": redact_pii(query), "retrieved_source_ids": [c.id for c in chunks], "similarity_scores": [round(c.score, 4) for c in chunks], "reranker_enabled": settings.reranker_enabled, "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"], "retrieval_ms": round(retrieval_ms, 2), "total_ms": round(total_ms, 2), "cost_usd": cost_for_tokens(usage["input_tokens"], usage["output_tokens"]), "citations": [c.id for c in citations], "refusal": refused, "pii_redacted": True, "error": None})
    return ChatResponse(answer=answer, citations=citations, refused=refused, request_id=request_id, metadata={"session_id": session.id, "top_score": top_score, "retrieval_ms": retrieval_ms, "total_ms": total_ms})

@app.get("/metrics")
def metrics():
    return {"chunks": len(retriever.chunks), "top_k": settings.top_k, "threshold": settings.low_confidence_threshold, "model": settings.claude_model}

from typing import Any, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str = Field(min_length=1, max_length=4000)
    language: Optional[str] = None

class Citation(BaseModel):
    id: str
    document: str
    page: int | None = None
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    refused: bool = False
    request_id: str
    metadata: dict[str, Any] = {}

class SessionResponse(BaseModel):
    session_id: str

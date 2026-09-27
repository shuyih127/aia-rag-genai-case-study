from dataclasses import dataclass, field
from collections import defaultdict
import uuid

@dataclass
class Turn:
    question: str
    answer: str

@dataclass
class Session:
    id: str
    turns: list[Turn] = field(default_factory=list)

# In-memory storage is sufficient for the demo. Production would use a durable,
# authenticated session store with retention and access controls.
SESSIONS: dict[str, Session] = {}

def new_session() -> Session:
    session = Session(str(uuid.uuid4()))
    SESSIONS[session.id] = session
    return session

def get_session(session_id: str | None) -> Session:
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    return new_session()

def standalone_query(question: str, session: Session) -> str:
    if not session.turns:
        return question
    # Lightweight deterministic rewrite; production can replace this with a
    # dedicated query-rewrite model or a conversation summarizer.
    previous = session.turns[-1].question
    pronoun = any(x in question.lower() for x in ["it", "that", "this", "它", "该"])
    return f"{previous} {question}" if pronoun else question

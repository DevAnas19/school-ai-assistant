"""
In-memory conversation store with per-session history.
Keeps last N messages for context window management.
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models.schemas import HistoryEntry

# session_id → list of messages
_store: Dict[str, List[dict]] = {}
# session_id → student_id
_session_meta: Dict[str, str] = {}

MAX_HISTORY = 20  # messages to keep per session


def init_session(session_id: str, student_id: str) -> None:
    if session_id not in _store:
        _store[session_id] = []
    _session_meta[session_id] = student_id


def add_message(session_id: str, role: str, content: str, intent: Optional[str] = None) -> None:
    if session_id not in _store:
        _store[session_id] = []

    _store[session_id].append({
        "role": role,
        "content": content,
        "intent": intent,
        "timestamp": datetime.now().isoformat()
    })

    # Trim to keep last MAX_HISTORY messages
    if len(_store[session_id]) > MAX_HISTORY:
        _store[session_id] = _store[session_id][-MAX_HISTORY:]


def get_messages_for_llm(session_id: str) -> List[dict]:
    """Return messages in OpenAI/Groq format (role + content only)."""
    msgs = _store.get(session_id, [])
    return [{"role": m["role"], "content": m["content"]} for m in msgs]


def get_history(session_id: str) -> List[HistoryEntry]:
    msgs = _store.get(session_id, [])
    return [
        HistoryEntry(
            role=m["role"],
            content=m["content"],
            timestamp=m["timestamp"],
            intent=m.get("intent")
        )
        for m in msgs
    ]


def get_student_id(session_id: str) -> Optional[str]:
    return _session_meta.get(session_id)


def list_sessions() -> List[str]:
    return list(_store.keys())


def clear_session(session_id: str) -> None:
    _store.pop(session_id, None)
    _session_meta.pop(session_id, None)

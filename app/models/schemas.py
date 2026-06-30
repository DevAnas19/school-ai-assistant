from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    student_id: Optional[str] = "STU001"
    session_id: Optional[str] = "default"


class ExecutionPlan(BaseModel):
    intent: str
    tools_selected: List[str]
    reasoning: str
    steps: List[str]


class ChatResponse(BaseModel):
    intent: str
    response: str
    data: Optional[Any] = None
    execution_plan: Optional[ExecutionPlan] = None
    status: str
    session_id: str
    timestamp: str


class HistoryEntry(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    intent: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    student_id: str
    history: List[HistoryEntry]
    total_messages: int


class LogEntry(BaseModel):
    timestamp: str
    session_id: str
    student_id: str
    user_query: str
    identified_intent: str
    tools_used: List[str]
    execution_time_ms: float
    response_summary: str
    status: str

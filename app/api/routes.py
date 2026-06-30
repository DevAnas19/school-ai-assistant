"""
FastAPI router for chat endpoints.
POST /chat       — Send a message to the ERP assistant
GET  /chat/history — Get conversation history for a session
GET  /logs       — View recent interaction logs (admin)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.chat_service import process_chat, get_chat_history
from app.utils.logger import read_logs

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message to the School ERP Assistant",
    description="""
Send a natural language query. The AI agent will:
1. Identify your intent
2. Select the appropriate ERP tool(s)
3. Fetch the data
4. Return a structured, human-readable response

**Example queries:**
- *Show my attendance for this month*
- *What are my Mathematics marks?*
- *Do I have any pending fees?*
- *What homework is due tomorrow?*
- *Show me tomorrow's timetable*
- *Summarize my academic performance*
- *Show my attendance, marks, and fees* *(multi-step)*
"""
)
async def chat(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = process_chat(
            message=request.message.strip(),
            student_id=request.student_id or "STU001",
            session_id=request.session_id or "default"
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Get conversation history",
    description="Returns all previous messages for a given session. Use session_id to track conversations."
)
async def chat_history(
    session_id: str = Query(default="default", description="Session identifier"),
    student_id: str = Query(default="STU001", description="Student ID")
):
    return get_chat_history(session_id=session_id, student_id=student_id)


# ─── Logs endpoint (bonus) ─────────────────────────────────────────────────────

logs_router = APIRouter(prefix="/logs", tags=["Logs"])


@logs_router.get(
    "",
    summary="View interaction logs",
    description="Returns recent interaction logs including query, intent, tools used, and execution time."
)
async def get_logs(limit: int = Query(default=20, ge=1, le=100)):
    return {
        "logs": read_logs(limit=limit),
        "count": limit
    }

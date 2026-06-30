"""
Chat service — wires together:
  memory → agent → logger → response
"""

import time
from datetime import datetime
from typing import Optional

from app.agents.erp_agent import run_agent
from app.memory import conversation as mem
from app.utils.logger import log_interaction
from app.models.schemas import ChatResponse, ChatHistoryResponse


def process_chat(
    message: str,
    student_id: str,
    session_id: str
) -> ChatResponse:
    """
    Main chat handler.
    1. Init/resume session memory
    2. Get conversation history for LLM context
    3. Run agent (plan → tool call → response)
    4. Store messages in memory
    5. Log interaction
    6. Return structured response
    """

    if not message or not message.strip():
        raise ValueError("Message cannot be empty.")

    # Init session if new
    mem.init_session(session_id, student_id)

    # Fetch previous messages for LLM context
    history = mem.get_messages_for_llm(session_id)

    start_time = time.time()

    try:
        response_text, intent, tools_used, raw_data, plan = run_agent(
            user_message=message,
            student_id=student_id,
            conversation_history=history
        )
        status = "success"
    except ValueError as e:
        # Config errors (e.g. missing API key)
        raise
    except Exception as e:
        response_text = f"I encountered an error while processing your request: {str(e)}"
        intent = "Error"
        tools_used = []
        raw_data = {}
        plan = None
        status = "error"

    exec_time_ms = (time.time() - start_time) * 1000

    # Store conversation turn in memory
    mem.add_message(session_id, "user", message)
    mem.add_message(session_id, "assistant", response_text, intent=intent)

    # Log the interaction
    log_interaction(
        session_id=session_id,
        student_id=student_id,
        user_query=message,
        identified_intent=intent,
        tools_used=tools_used,
        execution_time_ms=exec_time_ms,
        response_summary=response_text[:200],
        status=status
    )

    return ChatResponse(
        intent=intent,
        response=response_text,
        data=raw_data if raw_data else None,
        execution_plan=plan,
        status=status,
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )


def get_chat_history(session_id: str, student_id: str) -> ChatHistoryResponse:
    """Retrieve full conversation history for a session."""
    history = mem.get_history(session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        student_id=student_id,
        history=history,
        total_messages=len(history)
    )

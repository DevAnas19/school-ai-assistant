"""
School ERP AI Agent

Flow:
  User message
    → Build conversation context
    → Send to Groq LLM with tool definitions (function calling)
    → LLM selects tool(s) and arguments
    → Execute tool(s) from TOOL_REGISTRY
    → Send results back to LLM for natural language response generation
    → Return structured response
"""

import json
import time
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from groq import Groq

from app.tools.erp_tools import TOOL_REGISTRY, TOOL_DEFINITIONS
from app.models.schemas import ExecutionPlan


GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are SchoolBot, a smart and friendly AI assistant for a School ERP system.
You help students, teachers, and parents interact with school data using natural language.

Available ERP tools:
- get_attendance: Attendance records, percentages, monthly data
- get_marks: Subject-wise marks, grades, performance
- get_fees: Fee status, payment history, pending dues
- get_homework: Homework, assignments, due dates
- get_timetable: Class schedule, period timings

IMPORTANT GUIDELINES:
1. Always use the appropriate ERP tool(s) to fetch real data before responding.
2. For multi-part queries (e.g., "show my marks AND attendance"), call MULTIPLE tools.
3. Use conversation history to understand context — if the user says "which one is highest?", refer back to previously discussed data.
4. Be conversational, clear, and helpful. Format data in a readable way.
5. Always mention specific numbers, dates, and details from the fetched data.
6. If a query is ambiguous, make a reasonable assumption and state it.
7. Current date: """ + datetime.today().strftime("%A, %d %B %Y") + """

Never make up data. Only use what the tools return.
"""


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables.")
    return Groq(api_key=api_key)


def _extract_intent(tool_names: List[str]) -> str:
    """Derive a human-readable intent label from the tools selected."""
    if not tool_names:
        return "General Query"
    intent_map = {
        "get_attendance": "Attendance",
        "get_marks": "Marks & Grades",
        "get_fees": "Fee Status",
        "get_homework": "Homework",
        "get_timetable": "Timetable"
    }
    labels = [intent_map.get(t, t) for t in tool_names]
    return " + ".join(labels)


def _build_plan(tool_calls: List[Any], reasoning: str) -> ExecutionPlan:
    """Build an execution plan object from tool call data."""
    tool_names = [tc.function.name for tc in tool_calls] if tool_calls else []
    intent = _extract_intent(tool_names)
    steps = [
        "Received and parsed user query",
        f"Identified intent: {intent}",
        f"Selected ERP tools: {', '.join(tool_names) if tool_names else 'None'}",
        "Executed tool(s) and collected data",
        "Generated natural language response from retrieved data"
    ]
    return ExecutionPlan(
        intent=intent,
        tools_selected=tool_names,
        reasoning=reasoning,
        steps=steps
    )


def run_agent(
    user_message: str,
    student_id: str,
    conversation_history: List[dict]
) -> Tuple[str, str, List[str], Dict[str, Any], ExecutionPlan]:
    """
    Core agent execution.

    Returns:
        (natural_language_response, intent, tools_used, raw_tool_data, execution_plan)
    """
    client = _get_client()

    # Build full message list: system + history + current user message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # ── Step 1: LLM decides which tool(s) to call ─────────────────────────────
    first_response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        max_tokens=1024,
        temperature=0.1
    )

    first_msg = first_response.choices[0].message
    tool_calls = first_msg.tool_calls or []

    # ── Step 2: Execute each tool ─────────────────────────────────────────────
    tools_used = []
    all_tool_data = {}
    tool_results_messages = []

    if tool_calls:
        # Add assistant's tool-call decision to message chain
        messages.append(first_msg)

        for tc in tool_calls:
            fn_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            # Inject student_id if not already present
            args.setdefault("student_id", student_id)

            # Execute the tool
            if fn_name in TOOL_REGISTRY:
                try:
                    result = TOOL_REGISTRY[fn_name](**args)
                except Exception as e:
                    result = {"error": str(e), "tool": fn_name}
            else:
                result = {"error": f"Unknown tool: {fn_name}"}

            tools_used.append(fn_name)
            all_tool_data[fn_name] = result

            # Add tool result back to message chain
            tool_results_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result)
            })

        messages.extend(tool_results_messages)

        # ── Step 3: LLM generates final human-readable response ────────────────
        final_response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=1500,
            temperature=0.4
        )
        response_text = final_response.choices[0].message.content

        reasoning = f"User asked about {', '.join(tools_used)}. Tool(s) fetched live ERP data and AI synthesized the response."
        plan = _build_plan(tool_calls, reasoning)

    else:
        # No tool call — LLM answered from context/conversation memory
        response_text = first_msg.content or "I'm sorry, I couldn't process that request. Could you please rephrase?"
        reasoning = "Query answered from conversation context — no ERP data lookup required."
        plan = ExecutionPlan(
            intent="General Query",
            tools_selected=[],
            reasoning=reasoning,
            steps=[
                "Received and parsed user query",
                "Determined no ERP tool lookup required",
                "Generated response from conversation context"
            ]
        )

    intent = _extract_intent(tools_used)
    return response_text, intent, tools_used, all_tool_data, plan


def run_multi_step_agent(
    user_message: str,
    student_id: str,
    conversation_history: List[dict]
) -> Tuple[str, str, List[str], Dict[str, Any], ExecutionPlan]:
    """
    Alias for run_agent — Groq function calling already handles multi-tool scenarios.
    The LLM will automatically call multiple tools for compound queries.
    """
    return run_agent(user_message, student_id, conversation_history)

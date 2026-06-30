"""
Structured JSON logger for ERP assistant interactions.
Writes each request/response as a JSON line to logs/erp_assistant.log
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "erp_assistant.log"

# Standard Python logger for errors/debug
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("school_erp")


def log_interaction(
    session_id: str,
    student_id: str,
    user_query: str,
    identified_intent: str,
    tools_used: List[str],
    execution_time_ms: float,
    response_summary: str,
    status: str = "success"
) -> None:
    """Append a structured log entry as a JSON line."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "student_id": student_id,
        "user_query": user_query,
        "identified_intent": identified_intent,
        "tools_used": tools_used,
        "execution_time_ms": round(execution_time_ms, 2),
        "response_summary": response_summary[:200],  # cap length
        "status": status
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info(f"[{session_id}] intent={identified_intent} tools={tools_used} time={execution_time_ms:.0f}ms status={status}")


def read_logs(limit: int = 50) -> List[dict]:
    """Read last N log entries."""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE) as f:
        lines = f.readlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line.strip()))
        except Exception:
            pass
    return list(reversed(entries))

"""
ERP Tool implementations — each tool reads from mock JSON data
and returns structured results ready for the AI agent.
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, Optional

MOCK_DATA_DIR = Path(__file__).parent.parent.parent / "mock_data"


def _load(filename: str) -> Dict:
    with open(MOCK_DATA_DIR / filename) as f:
        return json.load(f)


# ─── Tool 1: Attendance ───────────────────────────────────────────────────────

def get_attendance(student_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Fetch attendance data for the student."""
    data = _load("attendance.json")

    if month:
        month_cap = month.capitalize()
        monthly = data.get("monthly", {})
        if month_cap in monthly:
            m = monthly[month_cap]
            return {
                "tool": "attendance",
                "student": data["name"],
                "period": month_cap,
                "total_days": m["total"],
                "days_present": m["present"],
                "days_absent": m["absent"],
                "percentage": m["percentage"],
                "status": "Good" if m["percentage"] >= 90 else "Low",
                "overall_percentage": data["attendance_percentage"]
            }

    return {
        "tool": "attendance",
        "student": data["name"],
        "class": data["class"],
        "academic_year": data["academic_year"],
        "total_working_days": data["total_working_days"],
        "days_present": data["days_present"],
        "days_absent": data["days_absent"],
        "attendance_percentage": data["attendance_percentage"],
        "monthly_breakdown": data["monthly"],
        "absent_dates": data["absent_dates"],
        "status": "Good" if data["attendance_percentage"] >= 90 else "Needs Improvement"
    }


# ─── Tool 2: Marks ───────────────────────────────────────────────────────────

def get_marks(student_id: str, subject: Optional[str] = None) -> Dict[str, Any]:
    """Fetch marks/grades for the student."""
    data = _load("marks.json")
    subjects = data["subjects"]

    if subject:
        sub_lower = subject.lower()
        match = next((s for s in subjects if sub_lower in s["subject"].lower()), None)
        if match:
            return {
                "tool": "marks",
                "student": data["name"],
                "subject": match["subject"],
                "teacher": match["teacher"],
                "obtained_marks": match["obtained_marks"],
                "max_marks": match["max_marks"],
                "grade": match["grade"],
                "percentage": match["percentage"],
                "exam_breakdown": match["exams"],
                "performance": _perf_label(match["percentage"])
            }
        return {"tool": "marks", "error": f"No records found for subject: {subject}"}

    highest = max(subjects, key=lambda s: s["obtained_marks"])
    lowest = min(subjects, key=lambda s: s["obtained_marks"])

    return {
        "tool": "marks",
        "student": data["name"],
        "class": data["class"],
        "semester": data["semester"],
        "subjects": subjects,
        "total_marks": data["total_marks"],
        "max_total_marks": data["max_total_marks"],
        "overall_percentage": data["overall_percentage"],
        "overall_grade": data["overall_grade"],
        "class_rank": data["class_rank"],
        "total_students": data["total_students"],
        "highest_scoring_subject": highest["subject"],
        "lowest_scoring_subject": lowest["subject"],
        "average_score": round(data["total_marks"] / len(subjects), 1)
    }


def _perf_label(pct: float) -> str:
    if pct >= 90: return "Excellent"
    if pct >= 75: return "Good"
    if pct >= 60: return "Average"
    return "Needs Improvement"


# ─── Tool 3: Fee Status ───────────────────────────────────────────────────────

def get_fees(student_id: str, filter_type: Optional[str] = None) -> Dict[str, Any]:
    """Fetch fee status and payment history."""
    data = _load("fees.json")

    if filter_type == "pending":
        pending = [f for f in data["fee_structure"] if f["pending"] > 0]
        return {
            "tool": "fees",
            "student": data["name"],
            "filter": "pending_only",
            "pending_items": pending,
            "total_pending": data["total_pending"],
            "upcoming_dues": data["upcoming_dues"]
        }

    if filter_type == "history":
        return {
            "tool": "fees",
            "student": data["name"],
            "filter": "payment_history",
            "payment_history": data["payment_history"],
            "total_paid": data["total_paid"]
        }

    return {
        "tool": "fees",
        "student": data["name"],
        "class": data["class"],
        "academic_year": data["academic_year"],
        "total_annual_fee": data["total_annual_fee"],
        "total_paid": data["total_paid"],
        "total_pending": data["total_pending"],
        "fee_structure": data["fee_structure"],
        "payment_history": data["payment_history"],
        "upcoming_dues": data["upcoming_dues"],
        "payment_status": "Cleared" if data["total_pending"] == 0 else "Partially Paid"
    }


# ─── Tool 4: Homework ─────────────────────────────────────────────────────────

def get_homework(student_id: str, filter_type: Optional[str] = None, subject: Optional[str] = None) -> Dict[str, Any]:
    """Fetch homework/assignment data."""
    data = _load("homework.json")
    hw_list = data["homework"]

    today = date.today().isoformat()
    tomorrow = (date.today().replace(day=date.today().day + 1)).isoformat() if date.today().day < 28 else None

    if filter_type == "pending":
        pending = [h for h in hw_list if h["status"] == "Pending"]
        return {"tool": "homework", "filter": "pending", "count": len(pending), "homework": pending}

    if filter_type == "overdue":
        overdue = [h for h in hw_list if h["status"] == "Overdue"]
        return {"tool": "homework", "filter": "overdue", "count": len(overdue), "homework": overdue}

    if filter_type == "today":
        today_hw = [h for h in hw_list if h["due_date"] == today]
        return {"tool": "homework", "filter": "due_today", "date": today, "count": len(today_hw), "homework": today_hw}

    if filter_type == "tomorrow" and tomorrow:
        tmrw_hw = [h for h in hw_list if h["due_date"] == tomorrow]
        return {"tool": "homework", "filter": "due_tomorrow", "date": tomorrow, "count": len(tmrw_hw), "homework": tmrw_hw}

    if subject:
        sub_hw = [h for h in hw_list if subject.lower() in h["subject"].lower()]
        return {"tool": "homework", "filter": f"subject:{subject}", "count": len(sub_hw), "homework": sub_hw}

    pending_count = sum(1 for h in hw_list if h["status"] == "Pending")
    overdue_count = sum(1 for h in hw_list if h["status"] == "Overdue")
    completed_count = sum(1 for h in hw_list if h["status"] == "Completed")

    return {
        "tool": "homework",
        "student": data["name"],
        "class": data["class"],
        "summary": {"pending": pending_count, "overdue": overdue_count, "completed": completed_count, "total": len(hw_list)},
        "homework": hw_list
    }


# ─── Tool 5: Timetable ───────────────────────────────────────────────────────

def get_timetable(student_id: str, day: Optional[str] = None, subject: Optional[str] = None) -> Dict[str, Any]:
    """Fetch class timetable."""
    data = _load("timetable.json")
    schedule = data["schedule"]

    today_name = datetime.today().strftime("%A")
    tomorrow_name = _next_day(today_name)

    if day:
        day_cap = day.capitalize()
        if day.lower() in ["today"]:
            day_cap = today_name
        elif day.lower() in ["tomorrow"]:
            day_cap = tomorrow_name

        day_schedule = schedule.get(day_cap)
        if day_schedule:
            return {
                "tool": "timetable",
                "day": day_cap,
                "class": data["class"],
                "periods": day_schedule,
                "first_class": day_schedule[0] if day_schedule else None,
                "total_periods": len(day_schedule)
            }
        return {"tool": "timetable", "error": f"No schedule found for: {day}"}

    if subject:
        sub_classes = []
        for day_name, periods in schedule.items():
            for p in periods:
                if subject.lower() in p["subject"].lower():
                    sub_classes.append({"day": day_name, **p})
        return {
            "tool": "timetable",
            "subject": subject,
            "classes": sub_classes,
            "total_classes_per_week": len(sub_classes)
        }

    return {
        "tool": "timetable",
        "class": data["class"],
        "academic_year": data["academic_year"],
        "today": today_name,
        "today_schedule": schedule.get(today_name, []),
        "full_schedule": schedule
    }


def _next_day(day: str) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    idx = days.index(day) if day in days else 0
    return days[(idx + 1) % 7]


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "get_attendance": get_attendance,
    "get_marks": get_marks,
    "get_fees": get_fees,
    "get_homework": get_homework,
    "get_timetable": get_timetable,
}

# Groq-compatible tool definitions for function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_attendance",
            "description": "Fetch student attendance data. Use for queries about attendance percentage, absent days, monthly attendance, or missed classes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "Student ID"},
                    "month": {"type": "string", "description": "Optional month name (e.g. January, June). Omit for full-year data."}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_marks",
            "description": "Fetch student marks/grades. Use for queries about scores, grades, best/worst subject, average marks, or exam results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "Student ID"},
                    "subject": {"type": "string", "description": "Optional subject name (e.g. Mathematics, Science). Omit for all subjects."}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fees",
            "description": "Fetch fee status, payment history, and pending dues. Use for queries about fee payment, pending fees, or payment history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "Student ID"},
                    "filter_type": {"type": "string", "enum": ["pending", "history", "all"], "description": "Filter: 'pending' for unpaid fees, 'history' for payment history, 'all' for complete summary."}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_homework",
            "description": "Fetch homework and assignment details. Use for queries about pending homework, due assignments, completed work, or overdue tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "Student ID"},
                    "filter_type": {"type": "string", "enum": ["pending", "overdue", "today", "tomorrow", "all"], "description": "Filter homework by status or due date."},
                    "subject": {"type": "string", "description": "Optional subject name to filter homework."}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_timetable",
            "description": "Fetch class timetable/schedule. Use for queries about class timings, which subject is next, first class, or schedule for a specific day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "Student ID"},
                    "day": {"type": "string", "description": "Day name (e.g. Monday, today, tomorrow). Omit for full weekly schedule."},
                    "subject": {"type": "string", "description": "Optional subject name to find when a subject is scheduled."}
                },
                "required": ["student_id"]
            }
        }
    }
]

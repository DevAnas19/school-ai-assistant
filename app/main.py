"""
School ERP AI Assistant — FastAPI Application
Run: uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router
from app.api.routes import logs_router

app = FastAPI(
    title="School ERP AI Assistant",
    description="""
## 🎓 AI-Powered School ERP Assistant

An intelligent assistant that lets **students, teachers, and parents** interact with school data using natural language.

### Features
- **Natural Language Understanding** — Ask anything in plain English
- **AI Agent Planning** — The AI decides which ERP tool(s) to use
- **Tool Calling** — Automated data retrieval from ERP modules
- **Conversation Memory** — Context-aware multi-turn conversations
- **Multi-Step Execution** — Handle compound queries in one message
- **Structured Responses** — Always returns clean, structured JSON

### ERP Modules Available
| Tool | Examples |
|------|---------|
| 📅 Attendance | "Show my attendance", "How many classes did I miss?" |
| 📝 Marks | "What are my Science marks?", "Which subject is my best?" |
| 💰 Fees | "Any pending fees?", "Show payment history" |
| 📚 Homework | "What homework is due?", "Show overdue assignments" |
| 🕐 Timetable | "Tomorrow's schedule", "When is my Maths class?" |

### Mock Student
- **Student ID:** STU001
- **Name:** Anas Khan, Class 10-A
""",
    version="1.0.0",
    contact={
        "name": "Anas Khan",
        "url": "https://github.com/DevAnas19"
    }
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routers
app.include_router(chat_router)
app.include_router(logs_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "School ERP AI Assistant",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat",
            "history": "GET /chat/history?session_id=<id>",
            "logs": "GET /logs"
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Unexpected server error", "detail": str(exc)}
    )
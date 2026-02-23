"""
Vintage Coach Bag Q&A Chatbot — FastAPI backend.
Serves the web UI and a POST /chat endpoint.
"""

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from chatbot import generate_answer

_BACKEND_UNAVAILABLE_MSG = (
    "Chat backend not configured. For local use, run Ollama (ollama run llama3.2). "
    "For GCP, set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION."
)

app = FastAPI(
    title="Vintage Coach Chatbot",
    description="Q&A chatbot for vintage Coach bags (serial numbers, era, hardware, care).",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    response: str
    safety_triggered: bool


@app.get("/")
def index():
    """Serve the chat UI."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Frontend not found")
    return FileResponse(index_file)


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """Get a single turn response from the chatbot."""
    try:
        result = generate_answer(body.message)
        return ChatResponse(
            response=result.response,
            safety_triggered=result.triggered,
        )
    except RuntimeError as e:
        msg = str(e)
        if "OPENAI_API_KEY" in msg or "GOOGLE_CLOUD_PROJECT" in msg or "VERTEX" in msg or "Ollama" in msg:
            raise HTTPException(
                status_code=503,
                detail="Chat backend not configured. For local use, run Ollama (ollama run llama3.2). Or set OPENAI_API_KEY, or on GCP set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION.",
            ) from e
        raise HTTPException(status_code=500, detail=msg) from e


@app.get("/health")
def health():
    """Health check for deployment."""
    return {"status": "ok"}

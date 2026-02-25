"""
Vintage Coach Bag Q&A Chatbot — FastAPI backend.
Serves the web UI and a POST /chat endpoint with stateful multi-turn sessions.
"""

import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from chatbot import build_initial_messages, generate_answer_from_messages

app = FastAPI(
    title="Vintage Coach Chatbot",
    description="Q&A chatbot for vintage Coach bags (serial numbers, era, hardware, care).",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Session storage: session_id -> list of messages (OpenAI format)
sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    images: list[str] | None = None  # base64 data URLs (data:image/...;base64,...)


class ChatResponse(BaseModel):
    response: str
    session_id: str
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
    """Get a response from the chatbot (multi-turn with session history)."""
    session_id = body.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = build_initial_messages()

    # Build user message: text only, or multimodal (text + images)
    # Validate images: max 5, each data URL reasonable size (~6MB base64 for ~4MB image)
    MAX_IMAGE_B64 = 6 * 1024 * 1024
    valid_images = [
        img for img in (body.images or [])[:5]
        if img and img.startswith("data:image/") and len(img) < MAX_IMAGE_B64
    ]
    if valid_images:
        content: list[dict] = [{"type": "text", "text": body.message}]
        for img in valid_images:
            if img and img.startswith("data:image/"):
                content.append({"type": "image_url", "image_url": {"url": img}})
        user_msg = {"role": "user", "content": content}
    else:
        user_msg = {"role": "user", "content": body.message}

    sessions[session_id].append(user_msg)
    try:
        result = generate_answer_from_messages(sessions[session_id], user_message=body.message)
        sessions[session_id].append({"role": "assistant", "content": result.response})
        return ChatResponse(
            response=result.response,
            session_id=session_id,
            safety_triggered=result.triggered,
        )
    except RuntimeError as e:
        sessions[session_id].pop()  # Roll back user message on error
        msg = str(e)
        if "GOOGLE_CLOUD_PROJECT" in msg or "VERTEX" in msg or "VERTEXAI" in msg:
            raise HTTPException(
                status_code=503,
                detail="Chat backend not configured. Create a .env file (see .env.example) with GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION, and run gcloud auth application-default login.",
            ) from e
        raise HTTPException(status_code=500, detail=msg) from e


@app.post("/clear")
def clear(session_id: str | None = None):
    """Clear a session. If session_id is provided and exists, it is removed."""
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"status": "ok"}


@app.get("/health")
def health():
    """Health check for deployment."""
    return {"status": "ok"}

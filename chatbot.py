"""Core chat logic for the Vintage Coach bag chatbot.

Backends:
- Vertex AI (Gemini) — GCP; set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION.
- Ollama — local open-source models; runs when Vertex isn't configured.

System prompt, few-shot examples, and safety backstop are shared.
"""

from __future__ import annotations

import os
from typing import Dict, List

import httpx

from prompt import get_few_shot_examples, get_system_prompt
from safety import SafetyResult, apply_safety_backstop

OLLAMA_DEFAULT_BASE = "http://localhost:11434"


def _use_vertex_ai() -> bool:
    """True if Vertex AI config is present (use Gemini on GCP)."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEX_AI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION")
    return bool(project and location)


def _ollama_endpoint() -> str:
    """Return the Ollama chat completions endpoint URL."""
    base = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE).rstrip("/")
    # Ollama's OpenAI-compatible endpoint is /v1/chat/completions
    return f"{base}/v1/chat/completions"


def _build_messages(user_message: str) -> List[Dict[str, str]]:
    """Construct chat-completions style messages."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": get_system_prompt()},
    ]
    for example in get_few_shot_examples():
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def _raw_answer_ollama(user_message: str, *, model: str | None = None) -> str:
    """Call a local Ollama model via its OpenAI-compatible HTTP API."""
    url = _ollama_endpoint()
    model_name = model or os.getenv("OLLAMA_MODEL", "llama3.2")

    payload = {
        "model": model_name,
        "messages": _build_messages(user_message),
        "temperature": 0.2,
    }
    resp = httpx.post(url, json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return (content or "").strip()


def _raw_answer_vertex(user_message: str, *, model: str | None = None) -> str:
    """Call a Vertex AI Gemini model."""
    import vertexai
    from vertexai.generative_models import Content, GenerativeModel, Part

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEX_AI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION")
    if not project or not location:
        raise RuntimeError(
            "Vertex AI requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION "
            "(or VERTEX_AI_PROJECT / VERTEX_AI_LOCATION)."
        )

    vertexai.init(project=project, location=location)
    model_id = model or os.getenv("VERTEX_AI_MODEL", "gemini-1.5-flash")

    generative_model = GenerativeModel(
        model_id,
        system_instruction=get_system_prompt(),
    )
    history: List[Content] = []
    for example in get_few_shot_examples():
        history.append(Content(role="user", parts=[Part.from_text(example["user"])]))
        history.append(
            Content(role="model", parts=[Part.from_text(example["assistant"])])
        )
    chat = generative_model.start_chat(history=history)
    response = chat.send_message(user_message)
    return (response.text or "").strip()


def raw_model_answer(user_message: str, *, model: str | None = None) -> str:
    """Call the configured LLM backend and return the raw answer."""
    if _use_vertex_ai():
        return _raw_answer_vertex(user_message, model=model)
    return _raw_answer_ollama(user_message, model=model)


def generate_answer(user_message: str, *, model: str | None = None) -> SafetyResult:
    """Generate an answer and run it through the safety backstop.

    Returns a SafetyResult where `.response` is either the original model
    answer or a safety fallback, depending on whether the backstop triggers.
    """
    raw = raw_model_answer(user_message, model=model)
    return apply_safety_backstop(raw, user_message=user_message)

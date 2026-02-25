"""Core chat logic for the Vintage Coach bag chatbot.

Uses LiteLLM with Vertex AI (Gemini). Requires GOOGLE_CLOUD_PROJECT and
GOOGLE_CLOUD_LOCATION. Uses Application Default Credentials.
"""

from __future__ import annotations

import os
from typing import Dict, List

from litellm import completion

from prompt import get_few_shot_examples, get_system_prompt
from safety import SafetyResult, apply_safety_backstop

MODEL = os.getenv("VERTEX_AI_MODEL", "vertex_ai/gemini-2.0-flash-lite")


def build_initial_messages() -> List[Dict[str, str]]:
    """Build the initial message list with system prompt and few-shot examples."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": get_system_prompt()},
    ]
    for example in get_few_shot_examples():
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    return messages


def _build_messages(user_message: str) -> List[Dict[str, str]]:
    """Construct chat-completions style messages for single turn."""
    messages = build_initial_messages()
    messages.append({"role": "user", "content": user_message})
    return messages


def _generate_response(messages: List[Dict], *, model: str | None = None) -> str:
    """Generate a response using LiteLLM with Vertex AI."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEX_AI_PROJECT") or os.getenv("VERTEXAI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION") or os.getenv("VERTEXAI_LOCATION")
    if not project or not location:
        raise RuntimeError(
            "Vertex AI requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION "
            "(or VERTEX_AI_PROJECT / VERTEX_AI_LOCATION)."
        )

    model_id = model or os.getenv("VERTEX_AI_MODEL", MODEL)
    if not model_id.startswith("vertex_ai/"):
        model_id = f"vertex_ai/{model_id}"

    response = completion(
        model=model_id,
        messages=messages,
        vertex_project=project,
        vertex_location=location,
        temperature=0.2,
    )
    content = response.choices[0].message.content if response.choices else ""
    return (content or "").strip()


def generate_answer(user_message: str, *, model: str | None = None) -> SafetyResult:
    """Generate an answer (single turn) and run it through the safety backstop."""
    messages = _build_messages(user_message)
    return generate_answer_from_messages(messages, user_message=user_message, model=model)


def _extract_text_from_content(content: str | list) -> str:
    """Extract text from message content (string or multimodal list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                parts.append(p.get("text", ""))
        return " ".join(parts)
    return ""


def generate_answer_from_messages(
    messages: List[Dict],
    *,
    user_message: str | None = None,
    model: str | None = None,
) -> SafetyResult:
    """Generate an answer from full message history and run it through the safety backstop.

    user_message: The last user message text (for safety backstop context). If None, derived from messages.
    """
    raw = _generate_response(messages, model=model)
    last_user = user_message
    if last_user is None and messages:
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = _extract_text_from_content(m.get("content", ""))
                break
    return apply_safety_backstop(raw, user_message=last_user or "")

"""
Post-generation safety backstop: keyword/regex/simple classifier.
Catches distressed or crisis-related content and medical-emergency content
the model may have engaged with, and returns a fallback response (crisis
resources or emergency-care guidance) instead.
"""

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Distressed / crisis keywords (lowercase; checked with word boundaries)
# ---------------------------------------------------------------------------

DISTRESSED_KEYWORDS = [
    "suicide",
    "suicidal",
    "kill myself",
    "killing myself",
    "end my life",
    "want to die",
    "want to end it",
    "self-harm",
    "self harm",
    "cut myself",
    "cutting myself",
    "hurt myself",
    "hurting myself",
    "overdose",
    "overdosing",
    "988",  # crisis line number often mentioned in distress
]

# ---------------------------------------------------------------------------
# Regex patterns for variants and phrases (distress)
# ---------------------------------------------------------------------------

DISTRESSED_PATTERNS = [
    re.compile(r"\b(how|want to|going to|should i)\s+(kill|hurt|end)\s+(my)?self\b", re.I),
    re.compile(r"\b(end\s+it\s+all|end\s+my\s+life)\b", re.I),
    re.compile(r"\b(commit\s+suicide)\b", re.I),
    re.compile(r"\b(no\s+reason\s+to\s+live)\b", re.I),
    re.compile(r"\b(crisis\s+line|suicide\s+hotline)\b", re.I),
]

# ---------------------------------------------------------------------------
# Danger / harm-to-others or unsafe-situation patterns
# ---------------------------------------------------------------------------

DANGER_PATTERNS = [
    # Intent to harm others
    re.compile(r"\b(hurt|harm|kill)\s+(someone|him|her|them)\b", re.I),
    # Being threatened or unsafe
    re.compile(r"\b(threatening\s+me|threatening\s+us)\b", re.I),
    re.compile(r"\b(don'?t|do\s+not|dont)\s+feel\s+safe\b", re.I),
    re.compile(r"\b(in\s+danger|unsafe|not\s+safe)\b", re.I),
]

# ---------------------------------------------------------------------------
# Medical emergency keywords (must be referred to doctor / hospital / 911)
# ---------------------------------------------------------------------------

MEDICAL_EMERGENCY_KEYWORDS = [
    "chest pain",
    "heart attack",
    "stroke",
    "can't breathe",
    "cant breathe",
    "difficulty breathing",
    "trouble breathing",
    "not breathing",
    "unconscious",
    "passed out",
    "seizure",
    "seizing",
    "severe allergic reaction",
    "anaphylaxis",
    "anaphylactic",
    "throat closing",
    "swelling throat",
    "severe bleeding",
    "heavy bleeding",
    "bleeding heavily",
    "poisoning",
    "poisoned",
    "overdose",
    "overdosed",
    "swallowed poison",
    "choking",
    "broken bone",
    "fracture",
    "head injury",
    "head trauma",
    "severe burn",
    "third degree burn",
    "go to the er",
    "go to the emergency room",
    "call 911",
    "call an ambulance",
    "emergency room",
    "emergency department",
]

# ---------------------------------------------------------------------------
# Regex patterns for medical emergencies
# ---------------------------------------------------------------------------

MEDICAL_EMERGENCY_PATTERNS = [
    re.compile(r"\b(call|dial)\s*911\b", re.I),
    re.compile(r"\b(go|get)\s+to\s+(the\s+)?(er|emergency|hospital)\b", re.I),
    re.compile(r"\b(having|having a)\s+(heart\s+attack|stroke)\b", re.I),
    re.compile(r"\b(signs?|symptoms?)\s+of\s+(stroke|heart\s+attack)\b", re.I),
    re.compile(r"\b(stroke|heart\s+attack)\s+(symptoms?|signs?)\b", re.I),
    re.compile(r"\b(can'?t|cannot)\s+breathe\b", re.I),
    re.compile(r"\b(severe|serious)\s+(pain|bleeding|injury)\b", re.I),
    re.compile(r"\b(need|needs)\s+(a\s+doctor|emergency\s+care|to\s+go\s+to\s+the\s+er)\b", re.I),
]

# ---------------------------------------------------------------------------
# Fallback responses when backstop triggers
# ---------------------------------------------------------------------------

SAFETY_FALLBACK_RESPONSE = """I'm really sorry you're feeling this way. I'm not able to help with self-harm, and I'm concerned about your safety.

If you or someone you know is in distress or crisis, please reach out to people who can help and talk to someone right away:

• **988 Suicide & Crisis Lifeline** (US): Call or text **988** — 24/7, free, confidential.
• **Crisis Text Line**: Text **HOME** to 741741 — 24/7, free, confidential crisis support to talk to someone.

If you are in immediate danger or this feels like an emergency, call **911** (US) or your local emergency number.

You are not alone in this. Please reach out to someone you trust or a crisis counselor for support."""

DANGER_FALLBACK_RESPONSE = """I'm really concerned about your safety and the safety of others. I'm not able to assist with anything that could cause harm.

If you or someone else is in danger or facing an emergency, please reach out for help right away:

• **In an emergency:** Call **911** (US) or your local emergency number so you can get immediate help and stay safe.
• **988 Suicide & Crisis Lifeline** (US): Call or text **988** — 24/7, free, confidential crisis support.
• **Crisis Text Line**: Text **HOME** to 741741 — 24/7, free, to talk to someone.

You are not alone — please reach out to trusted friends, family, or professional support. They can help you stay safe and get support."""

MEDICAL_EMERGENCY_FALLBACK_RESPONSE = """I can't give medical advice or diagnose emergencies. This sounds like something that needs immediate professional care.

• **If this is a medical emergency:** Call **911** (US) or your local emergency number, or go to the nearest emergency room.
• **If it's not an emergency but you need medical advice:** See a doctor, go to an urgent-care clinic, or call a nurse line (e.g. your insurance or local hospital).

Don't rely on this chat for medical decisions."""


@dataclass
class SafetyResult:
    """Result of the safety backstop check."""

    response: str
    triggered: bool
    source: str | None = None  # "user" | "generation" | None
    trigger_type: str | None = None  # "distress" | "danger" | "medical_emergency" | None


def _contains_distressed_content(text: str) -> bool:
    """Return True if text contains distressed keywords or patterns."""
    if not text or not text.strip():
        return False
    lower = text.lower()
    for kw in DISTRESSED_KEYWORDS:
        if kw in lower:
            return True
    for pat in DISTRESSED_PATTERNS:
        if pat.search(text):
            return True
    return False


def _contains_danger_content(text: str) -> bool:
    """Return True if text suggests someone else is in danger or being harmed."""
    if not text or not text.strip():
        return False
    for pat in DANGER_PATTERNS:
        if pat.search(text):
            return True
    return False


def _contains_medical_emergency_content(text: str) -> bool:
    """Return True if text contains medical-emergency keywords or patterns."""
    if not text or not text.strip():
        return False
    lower = text.lower()
    for kw in MEDICAL_EMERGENCY_KEYWORDS:
        if kw in lower:
            return True
    for pat in MEDICAL_EMERGENCY_PATTERNS:
        if pat.search(text):
            return True
    return False


def apply_safety_backstop(
    generated_text: str,
    user_message: str | None = None,
    *,
    fallback: str | None = None,
    medical_fallback: str | None = None,
    danger_fallback: str | None = None,
) -> SafetyResult:
    """Run a post-generation backstop: if user or model output suggests distress or medical emergency, return fallback.

    Checks both the user message and the model's generated text. Distress
    (crisis/mental health) is checked first; then medical emergency. If either
    triggers, returns the corresponding fallback response instead of the generation.

    Args:
        generated_text: The model's raw response.
        user_message: The last user message (optional; checked for distress and medical emergency).
        fallback: Override the default crisis-resources message if provided.
        medical_fallback: Override the default medical-emergency message if provided.

    Returns:
        SafetyResult with .response (original or fallback), .triggered (bool),
        .source ("user" | "generation" | None), and .trigger_type ("distress" | "medical_emergency" | None).
    """
    distress_fallback = fallback if fallback is not None else SAFETY_FALLBACK_RESPONSE
    medical_fallback_out = (
        medical_fallback if medical_fallback is not None else MEDICAL_EMERGENCY_FALLBACK_RESPONSE
    )
    danger_fallback_out = danger_fallback if danger_fallback is not None else DANGER_FALLBACK_RESPONSE

    # Check user message first (distress, then medical)
    if user_message:
        if _contains_distressed_content(user_message):
            return SafetyResult(
                response=distress_fallback, triggered=True, source="user", trigger_type="distress"
            )
        if _contains_danger_content(user_message):
            return SafetyResult(
                response=danger_fallback_out,
                triggered=True,
                source="user",
                trigger_type="danger",
            )
        if _contains_medical_emergency_content(user_message):
            return SafetyResult(
                response=medical_fallback_out,
                triggered=True,
                source="user",
                trigger_type="medical_emergency",
            )

    # Check generation (distress, then medical)
    if _contains_distressed_content(generated_text):
        return SafetyResult(
            response=distress_fallback, triggered=True, source="generation", trigger_type="distress"
        )
    if _contains_danger_content(generated_text):
        return SafetyResult(
            response=danger_fallback_out,
            triggered=True,
            source="generation",
            trigger_type="danger",
        )
    if _contains_medical_emergency_content(generated_text):
        return SafetyResult(
            response=medical_fallback_out,
            triggered=True,
            source="generation",
            trigger_type="medical_emergency",
        )

    return SafetyResult(response=generated_text, triggered=False, source=None, trigger_type=None)


def is_safe(generated_text: str, user_message: str | None = None) -> bool:
    """Return False if the backstop would trigger (user or generation has distressed or medical-emergency content)."""
    if user_message:
        if _contains_distressed_content(user_message) or _contains_medical_emergency_content(
            user_message
        ):
            return False
    if _contains_distressed_content(generated_text) or _contains_medical_emergency_content(
        generated_text
    ):
        return False
    return True

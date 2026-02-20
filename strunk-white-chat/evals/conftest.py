"""Shared fixtures for Strunk & White style checker evals.

Provides two core helpers:
  - `get_review`: sends text to the style checker bot, returns its response.
  - `judge_with_golden`: judges a response against a golden reference (1-10).
  - `judge_with_rubric`: judges a response against weighted rubric criteria (1-10).
"""

import json
import sys
from pathlib import Path

from litellm import completion

# Add parent directory so we can import app.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import MODEL, build_initial_messages

# --- Bot (the system under test) ---

JUDGE_MODEL = "vertex_ai/gemini-2.0-flash"


def get_review(text: str) -> str:
    """Send text to the Strunk & White bot and return its response."""
    messages = build_initial_messages()
    messages.append({"role": "user", "content": text})
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content


# --- Judge helpers ---

JUDGE_SYSTEM_GOLDEN = """\
You are an expert evaluator. Given a user prompt, a reference response, and a \
generated response, please rate the overall quality of the generated response \
on a scale of 1 to 10 based on how well it compares to the reference response. \
Consider factors such as accuracy, completeness, coherence, and helpfulness \
when comparing to the reference. The reference response represents a \
high-quality answer that you should use as a benchmark. Start your response \
with a valid JSON object. The JSON object should contain a single key "rating" \
and the value should be an integer between 1 and 10.

Example response:
{
  "rating": 7
}"""

JUDGE_SYSTEM_RUBRIC = """\
You are an expert evaluator. Given a user prompt, a generated response, and a \
list of quality rubrics, please rate the overall quality of the response on a \
scale of 1 to 10 based on how well it satisfies the rubrics. Consider all \
rubrics holistically when determining your score. A response that violates \
multiple rubrics should receive a lower score, while a response that satisfies \
all rubrics should receive a higher score. Start your response with a valid \
JSON object. The JSON object should contain a single key "rating" and the \
value should be an integer between 1 and 10.

Example response:
{
  "rating": 7
}"""


def judge_with_golden(prompt: str, reference: str, response: str) -> int:
    """Judge a response against a golden reference. Returns rating 1-10."""
    user_msg = (
        "Given the following prompt, reference response, and generated "
        "response, please rate the overall quality of the generated response "
        "on a scale of 1 to 10 based on how well it compares to the reference."
        f"\n\n<prompt>\n{prompt}\n</prompt>"
        f"\n\n<reference_response>\n{reference}\n</reference_response>"
        f"\n\n<generated_response>\n{response}\n</generated_response>"
    )
    result = completion(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_GOLDEN},
            {"role": "user", "content": user_msg},
        ],
    )
    return _parse_rating(result.choices[0].message.content)


def judge_with_rubric(prompt: str, response: str, rubric: str) -> int:
    """Judge a response against a rubric. Returns rating 1-10."""
    user_msg = (
        "Given the following prompt, response, and rubrics, please rate the "
        "overall quality of the response on a scale of 1 to 10 based on how "
        "well it satisfies the rubrics."
        f"\n\n<prompt>\n{prompt}\n</prompt>"
        f"\n\n<response>\n{response}\n</response>"
        f"\n\n<rubrics>\n{rubric}\n</rubrics>"
    )
    result = completion(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_RUBRIC},
            {"role": "user", "content": user_msg},
        ],
    )
    return _parse_rating(result.choices[0].message.content)


def _parse_rating(text: str) -> int:
    """Extract the integer rating from the judge's JSON response."""
    start = text.index("{")
    end = text.index("}", start) + 1
    return int(json.loads(text[start:end])["rating"])

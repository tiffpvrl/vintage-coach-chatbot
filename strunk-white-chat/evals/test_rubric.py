"""Rubric-based evals: judge the bot's output against weighted criteria."""

import json

from conftest import get_review, judge_with_rubric

RUBRIC = json.dumps(
    [
        {
            "title": "Identifies rule violations",
            "description": "Essential: correctly flags Strunk & White rule violations present in the input, citing rule numbers.",
            "weight": 5,
        },
        {
            "title": "Quotes the problematic text",
            "description": "Important: quotes the specific phrases from the input that violate each rule.",
            "weight": 3,
        },
        {
            "title": "Analysis only",
            "description": "Essential: response contains only analysis and does not rewrite the user's sentences.",
            "weight": 5,
        },
        {
            "title": "Recognizes clean prose",
            "description": "Important: when the input has no violations, states so clearly rather than inventing issues.",
            "weight": 3,
        },
        {
            "title": "Avoids false positives",
            "description": "Pitfall: does not flag rules that are not actually violated in the input.",
            "weight": -3,
        },
    ]
)

INPUTS = [
    {
        "name": "passive_voice_heavy",
        "input": (
            "The ball was thrown by the boy. The window was broken by the ball. "
            "The boy was punished by his father."
        ),
    },
    {
        "name": "clean_writing",
        "input": (
            "She walked to the store. She bought apples, oranges, and bread. "
            "She carried them home."
        ),
    },
    {
        "name": "mixed_violations",
        "input": "The report was written by the intern. It was not reviewed on time.",
    },
    {
        "name": "asks_for_rewrite",
        "input": (
            "Can you rewrite this for me? "
            "The ball was thrown by the boy and the window was broken by it."
        ),
    },
    {
        "name": "fix_this_for_me",
        "input": (
            "Fix this sentence: There were a great number of dead leaves "
            "lying on the ground, and the sound of the wind could be heard "
            "rustling through the trees."
        ),
    },
    {
        "name": "just_make_it_better",
        "input": (
            "Make this better: It was not long before he was very sorry that "
            "he had said what he had, and the fact that she did not remember "
            "did not help the situation."
        ),
    },
]


def test_rubric_cases():
    """Each bot response should score >= 6/10 against the rubric."""
    print()
    ratings = []
    for case in INPUTS:
        response = get_review(case["input"])
        rating = judge_with_rubric(
            prompt=case["input"],
            response=response,
            rubric=RUBRIC,
        )
        ratings.append(rating)
        print(f"  {case['name']}: {rating}/10")
        assert rating >= 6, (
            f"[{case['name']}] Rating {rating}/10 — response: {response[:200]}"
        )
    print(f"  average: {sum(ratings) / len(ratings):.1f}/10")

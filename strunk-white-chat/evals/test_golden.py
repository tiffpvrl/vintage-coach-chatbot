"""Golden-example evals: judge the bot's output against reference answers."""

from conftest import get_review, judge_with_golden

GOLDEN_EXAMPLES = [
    {
        "name": "passive_and_loose",
        "input": (
            "There were many participants who were involved in the study, and "
            "the results were published by the researchers, and the findings "
            "were very significant."
        ),
        "reference": (
            '- Rule 11 (active voice): "There were many participants who were '
            'involved" — passive and indirect.\n'
            '- Rule 11 (active voice): "the results were published by the '
            'researchers" — passive construction.\n'
            '- Rule 13 (omit needless words): "participants who were involved" '
            '— "who were involved" is padding.\n'
            '- Rule 14 (loose sentences): Three clauses chained with "and" '
            "creates a monotonous rhythm.\n\n"
            "The sentence packs several ideas into one breath; splitting and "
            "activating the verbs would sharpen each point."
        ),
    },
    {
        "name": "clean_prose",
        "input": (
            "The engineer designed the bridge. She calculated the load "
            "requirements, tested the materials, and documented each decision."
        ),
        "reference": (
            "No violations found. The writing is direct, active, and uses "
            "parallel construction with the Oxford comma."
        ),
    },
    {
        "name": "comma_splice_and_dangling_modifier",
        "input": (
            "However, being that the project was not completed on time, it was "
            "the case that the team did not meet the client's expectations, "
            "the funding was cut."
        ),
        "reference": (
            '- Rule 13 (omit needless words): "it was the case that" — '
            "padding; cut entirely.\n"
            "- Rule 12 (positive form): \"did not meet the client's "
            'expectations" — rephrase positively ("fell short of" or '
            '"missed").\n'
            '- Rule 11 (active voice): "the funding was cut" — passive; '
            "name who cut it.\n"
            "- Rule 5 (comma splice): \"the team did not meet the client's "
            'expectations, the funding was cut" — two independent clauses '
            "joined by a bare comma.\n"
            '- Rule 7 (dangling modifier): "being that the project was not '
            'completed on time" — dangling participial phrase with no clear '
            "grammatical subject.\n\n"
            "Nearly every clause here can be tightened; start by breaking it "
            "into two active sentences."
        ),
    },
]


def test_golden_examples():
    """Each bot response should score >= 6/10 against its golden reference."""
    print()
    ratings = []
    for example in GOLDEN_EXAMPLES:
        response = get_review(example["input"])
        rating = judge_with_golden(
            prompt=example["input"],
            reference=example["reference"],
            response=response,
        )
        ratings.append(rating)
        print(f"  {example['name']}: {rating}/10")
        assert rating >= 6, (
            f"[{example['name']}] Rating {rating}/10 — response: {response[:200]}"
        )
    print(f"  average: {sum(ratings) / len(ratings):.1f}/10")

"""Rule-detection evals: verify the bot flags specific rule numbers."""

from conftest import get_review

RULE_CASES = [
    {
        "name": "rule_11_passive_voice",
        "input": "The experiment was conducted by the students.",
        "expected": "Rule 11",
    },
    {
        "name": "rule_5_comma_splice",
        "input": "The sun was setting, the sky turned orange.",
        "expected": "Rule 5",
    },
    {
        "name": "rule_13_needless_words",
        "input": "He is a man who is very ambitious and driven.",
        "expected": "Rule 13",
    },
    {
        "name": "rule_7_dangling_modifier",
        "input": "Walking through the park, the trees were beautiful.",
        "expected": "Rule 7",
    },
    {
        "name": "rule_12_negative_form",
        "input": "She did not remember his name. He was not honest about it.",
        "expected": "Rule 12",
    },
    {
        "name": "w17_less_vs_fewer",
        "input": "There were less people at the meeting than expected.",
        "expected": "W17",
    },
]


def test_rule_detection():
    """Bot should mention the expected rule number in its response."""
    print()
    passed = 0
    for case in RULE_CASES:
        response = get_review(case["input"])
        found = case["expected"] in response
        passed += found
        print(f"  {case['name']}: {'PASS' if found else 'FAIL'}")
        assert found, f"[{case['name']}] Expected {case['expected']} in: {response}"
    print(f"  passed: {passed}/{len(RULE_CASES)}")

#!/usr/bin/env python3
"""
Vintage Coach Chatbot — evaluation harness.

Run from project root:
  uv run python eval/run_eval.py

Person 1 (LLM + Evaluation Lead) will implement:
- Golden dataset (20+ cases: 10 in-domain, 5 out-of-scope, 5 adversarial/safety)
- Deterministic metrics (e.g. refusal/safety keyword checks)
- MaaJ golden-reference and rubric evals
- Pass/fail per test and pass rate by category
"""
from __future__ import annotations

import sys

def main() -> int:
    print("Eval harness not yet implemented. Person 1: add golden dataset and run_eval logic.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

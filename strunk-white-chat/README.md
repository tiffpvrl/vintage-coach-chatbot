# Strunk & White Style Checker

A writing style checker chatbot grounded in *The Elements of Style* by Strunk & White. Paste your writing and the bot identifies rule violations with quoted evidence — without rewriting your text for you.

## Prerequisites

You need Google Cloud set up with Vertex AI. See the **Google Cloud & Vertex AI Setup Guide**.

Create a `.env` file in this directory:

```
VERTEXAI_PROJECT=your-project-id
VERTEXAI_LOCATION=us-central1
```

## Running

```bash
uv run python app.py
```

Open http://localhost:8000 in your browser.

## API

- `GET /` - Serves the style checker UI
- `POST /chat` - Send writing for review, returns style analysis
- `POST /clear` - Clear session history

## Evals

The `evals/` directory contains pytest-based evaluations using Model-as-a-Judge:

- `test_golden.py` - Judge bot responses against golden reference answers
- `test_rubric.py` - Judge bot responses against weighted rubric criteria
- `test_rules.py` - Verify the bot flags correct Strunk & White rule numbers

```bash
uv run pytest evals/ -v
```

Note: evals make live LLM calls to both the bot and a judge model, so they require network access and will incur API costs.

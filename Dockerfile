# Vintage Coach Chatbot — image for GCP Cloud Run
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Project files
COPY pyproject.toml README.md ./
COPY main.py chatbot.py prompt.py safety.py ./
COPY static/ ./static/

# Install dependencies and project (no dev)
RUN uv sync --no-dev

EXPOSE 8080

ENV HOST=0.0.0.0
ENV PORT=8080

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

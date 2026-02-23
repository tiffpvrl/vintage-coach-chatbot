# Vintage Coach Bag Q&A Chatbot

A narrow-domain chatbot that answers questions about **vintage Coach bags (pre-2000)**:
serial numbers and style numbers, era context and hardware, quality and damage inspection, and condition-based care.

## Scope

- **In scope:** Serial/style number interpretation, era and hardware identification, damage inspection, cleaning and conditioning, storage, and when to seek professional repair.
- **Out of scope (redirected):** Market valuation and pricing, medical/health advice, and final authentication or counterfeit appraisal.

## LLM backend (pick one)

Backend order: **Vertex AI** → **Ollama** (first configured wins).

| Backend | When to use | Config |
|--------|----------------|--------|
| **Ollama (local, open-source)** | Local dev **without any API key** | Install [Ollama](https://ollama.com), run a model (e.g. `ollama run llama3.2`). Optional: `OLLAMA_BASE_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3.2`). |
| **Vertex AI (Gemini)** | GCP (Cloud Run); no API key | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`; optional `VERTEX_AI_MODEL` (default `gemini-1.5-flash`) |

With no Vertex env vars set, the app uses **Ollama** by default (if Ollama is running). On Cloud Run, set Vertex env vars and use Vertex AI.

## Run locally (with Ollama — no API key)

1. **Install [Ollama](https://ollama.com)** and pull a model:
   ```bash
   ollama pull llama3.2
   ```
   (Other options: `mistral`, `llama3.1`, `gemma2:2b`.)

2. **Install the app** with [uv](https://docs.astral.sh/uv/):
   ```bash
   uv sync
   ```

3. **Start the app** (no env vars needed if Ollama is at `localhost:11434`):
   ```bash
   uv run uvicorn main:app --reload
   ```

4. Open **http://127.0.0.1:8000** and ask a question. The chatbot uses your local Ollama model.

To force Ollama when you also have an API key set: `set LLM_BACKEND=ollama`. To use a different model: `set OLLAMA_MODEL=mistral`.

## Run locally (Vertex AI from your machine)

Install [gcloud CLI](https://cloud.google.com/sdk/docs/install), run:
```bash
gcloud auth application-default login
set GOOGLE_CLOUD_PROJECT=your-gcp-project-id
set GOOGLE_CLOUD_LOCATION=us-central1
uv run uvicorn main:app --reload
```

## Run evaluation

From the project root:

```bash
uv run python eval/run_eval.py
```

(See `eval/README.md` or the eval script for options. Requires Vertex AI env vars or a local Ollama model.)

## Live URL

**Live app:** [Add your GCP deployment URL here after deploying.]

## Repo layout

- `main.py` — FastAPI app (GET `/`, POST `/chat`, GET `/health`)
- `chatbot.py` — Chat logic (prompt + LLM + safety backstop)
- `prompt.py` — System prompt, few-shot examples, scope, escape hatch
- `safety.py` — Post-generation safety backstop (distress / medical)
- `static/index.html` — Simple web UI
- `eval/` — Golden dataset and runnable eval script
- `pyproject.toml` — uv-based project config
- `Dockerfile` — For GCP (e.g. Cloud Run) deployment

## Deployment (GCP) with Vertex AI

1. **Enable APIs** in your project:
   - Vertex AI API
   - Cloud Run (if using Cloud Run)

2. **Grant the Cloud Run service account** access to Vertex AI:
   - IAM: add role **Vertex AI User** (or **roles/aiplatform.user**) to the service account that runs the Cloud Run service (default: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`).

3. **Deploy** (no API key needed when using Vertex AI):
   ```bash
   gcloud run deploy vintage-coach-chatbot --source . --region us-central1 --allow-unauthenticated \
     --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1"
   ```
   Replace `YOUR_PROJECT_ID` with your GCP project ID. The running container uses Application Default Credentials, so the service account above is used for Vertex AI calls.

4. Optional: set `VERTEX_AI_MODEL` (e.g. `gemini-1.5-pro`) if you want a different model than `gemini-1.5-flash`.

5. Put the live URL in this README and in your submission.

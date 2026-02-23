# Vintage Coach Bag Q&A Chatbot

A narrow-domain chatbot that answers questions about **vintage Coach bags (pre-2000)**:
serial numbers and style numbers, era context and hardware, quality and damage inspection, and condition-based care.

## Scope

- **In scope:** Serial/style number interpretation, era and hardware identification, damage inspection, cleaning and conditioning, storage, and when to seek professional repair.
- **Out of scope (redirected):** Market valuation and pricing, medical/health advice, and final authentication or counterfeit appraisal.

## LLM backend

Uses **LiteLLM** with **Vertex AI (Gemini)**. No API key needed — uses Application Default Credentials.

| Config | Required |
|--------|----------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | e.g. `us-central1` |
| `VERTEX_AI_MODEL` | Optional; default `vertex_ai/gemini-2.0-flash-lite` |

## Run locally

1. **Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)** and authenticate:
   ```bash
   gcloud auth application-default login
   ```

2. **Install the app** with [uv](https://docs.astral.sh/uv/):
   ```bash
   uv sync
   ```

3. **Create a `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your GCP project ID and location:
   ```
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

4. **Start the app**:
   ```bash
   uv run uvicorn main:app --reload
   ```

5. Open **http://127.0.0.1:8000** and ask a question.

   > **Windows:** If you get `WinError 10013` (socket access forbidden), another program may be using port 8000. Either terminate that process (e.g. `netstat -ano | findstr :8000` to find the PID, then `taskkill /PID <pid> /F`) or use a different port: `uv run uvicorn main:app --reload --port 8080`.

## Run evaluation

From the project root:

```bash
uv run python eval/run_eval.py
```

(See `eval/README.md` or the eval script for options. Requires Vertex AI env vars.)

## Live URL

**Live app:** [Add your GCP deployment URL here after deploying.]

## Repo layout

- `main.py` — FastAPI app (GET `/`, POST `/chat`, POST `/clear`, GET `/health`)
- `chatbot.py` — Chat logic (LiteLLM + Vertex AI + safety backstop)
- `prompt.py` — System prompt, few-shot examples, scope, escape hatch
- `safety.py` — Post-generation safety backstop (distress / medical)
- `static/index.html` — Simple web UI
- `eval/` — Golden dataset and runnable eval script
- `pyproject.toml` — uv-based project config
- `.env.example` — Template for local env vars (copy to `.env`)
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

4. Optional: set `VERTEX_AI_MODEL` (e.g. `vertex_ai/gemini-1.5-pro`) if you want a different model than `vertex_ai/gemini-2.0-flash-lite`.

5. Put the live URL in this README and in your submission.

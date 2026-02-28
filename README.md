# Vintage Coach Bag Q&A Chatbot

A narrow-domain chatbot that answers questions about **vintage Coach bags (pre-2000)**. It helps owners and shoppers interpret serial numbers, identify eras and hardware, inspect for damage, and learn how to clean, condition, and care for their bags.

## What you can ask

The chatbot specializes in four areas. Here are example questions to get you started:

### Serial & style numbers

- *"What does F5D-9966 mean on my Coach bag?"*
- *"My creed stamp says No. C7D-9085. What year was it made?"*
- *"I found a bag with 4582-371 stamped inside. What format is that?"*
- *"I can't find a serial number anywhere. Does that mean it's fake?"*

### Era & hardware

- *"How can I tell what era my bag is from? It has a turnlock and says Coach Leatherware inside."*
- *"My bag says Made in United States but not New York City. When is it from?"*
- *"What characteristics should I look for to authenticate a vintage Coach bag from the 1980s?"*
- *"The Coach logo on my bag looks different from photos online. Should I be worried?"*

### Care & cleaning

- *"My bag has mildew and a musty smell from storage. What should I do?"*
- *"The brass hardware is turning green. How do I clean it?"*
- *"My British Tan bag feels stiff and the corners are scuffed. Is that fixable?"*
- *"I have a dark stain and uneven color. How can I fix the discoloration?"*
- *"What's the best way to store a vintage Coach bag?"*

### Damage inspection & repair

- *"The strap cracked near the hardware. Can I fix it myself?"*
- *"How do I assess if damage is worth repairing?"*
- *"What are the critical inspection points before buying a vintage Coach bag?"*

### Attach images

You can also **attach photos** (e.g. of the creed, serial number, or hardware) to your questions. Use the + button in the query box or paste an image with Ctrl+V.

---

## Scope

- **In scope:** Serial/style number interpretation, era and hardware identification, damage inspection, cleaning and conditioning, storage, and when to seek professional repair.
- **Out of scope (redirected):** Market valuation and pricing, medical/health advice, and final authentication or counterfeit appraisal.

## LLM backend

Uses **LiteLLM** with **Vertex AI (Gemini)**. No API key needed — uses Application Default Credentials.


| Config                  | Required                                            |
| ----------------------- | --------------------------------------------------- |
| `GOOGLE_CLOUD_PROJECT`  | Your GCP project ID                                 |
| `GOOGLE_CLOUD_LOCATION` | e.g. `us-central1`                                  |
| `VERTEX_AI_MODEL`       | Optional; default `vertex_ai/gemini-2.0-flash-lite` |


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
5. Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** and ask a question. You can attach images (e.g. of a creed or serial number) to your questions.
  > **Windows:** If you get `WinError 10013` (socket access forbidden), another program may be using port 8000. Either terminate that process (e.g. `netstat -ano | findstr :8000` to find the PID, then `taskkill /PID <pid> /F`) or use a different port: `uv run uvicorn main:app --reload --port 8080`.

## Run evaluation

From the project root:

```bash
uv run python eval/run_eval.py
```

This tests the deployed chatbot. See `eval/README_eval.md` for full details. Requires Vertex AI env vars for the MaaS judge.

## Live URL

**Live app:** [https://vintage-coach-chatbot-718451494976.us-central1.run.app](https://vintage-coach-chatbot-718451494976.us-central1.run.app) 

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

---

## Technical design & components

This section describes the architecture, data flow, and implementation details of the Vintage Coach chatbot.

### Architecture overview

The system follows a layered design:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Static HTML    │────▶│  FastAPI        │────▶│  LiteLLM        │
│  (index.html)   │     │  (main.py)      │     │  + Vertex AI    │
│                 │     │                 │     │  (chatbot.py)   │
│  Client-side    │     │  Session store  │     │                 │
│  JS fetch      │     │  Multimodal     │     │  prompt.py      │
│  /chat POST    │     │  validation     │     │  safety.py      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Frontend:** Single-page HTML with vanilla JS; no build step. Uses fetch for POST `/chat`, maintains `session_id` for multi-turn.
- **Backend:** FastAPI app with in-memory session storage. Each request is validated, then routed to the chatbot module.
- **LLM layer:** LiteLLM abstracts Vertex AI (Gemini). Uses Application Default Credentials; no API keys.

### Request flow

1. User submits text (and optionally images) via the form.
2. **main.py** receives `ChatRequest`; validates `message` (1–4000 chars) and `images` (max 5, base64 data URLs, ~6MB each).
3. Session is created or resumed: `sessions[session_id]` holds a list of messages in OpenAI format.
4. User message is built as text-only or multimodal (text + `image_url` parts).
5. **chatbot.py** calls `generate_answer_from_messages()`: sends full history to LiteLLM, receives raw response.
6. **safety.py** runs `apply_safety_backstop()` on user + generation; may replace output with fallback.
7. Response is returned; assistant message is appended to session; `ChatResponse` sent to client.

### Component breakdown


| Component             | Purpose                                                                                                                                                                          |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **main.py**           | FastAPI app; routes (`/`, `/chat`, `/clear`, `/health`); session storage; request/response models; image validation and multimodal message construction.                         |
| **chatbot.py**        | Builds initial messages (system + few-shot), calls LiteLLM `completion()`, passes to safety backstop. Handles multimodal content extraction for safety context.                  |
| **prompt.py**         | System prompt assembly: role persona, hard-coded rules (serial numbers, era, hardware, damage, care), in-scope/out-of-scope instructions, escape hatch, and 6 few-shot examples. |
| **safety.py**         | Post-generation backstop: keyword + regex checks for distress/crisis and medical-emergency content; returns fallback responses when triggered.                                   |
| **static/index.html** | Chat UI: query box with + button, image paste, inline preview; chat pane with images-first layout; Markdown rendering (marked + DOMPurify).                                      |


### Message format & session management

Each session stores messages in OpenAI chat-completions format:

```python
[
  {"role": "system", "content": "<full system prompt>"},
  {"role": "user", "content": "<few-shot user>"},
  {"role": "assistant", "content": "<few-shot assistant>"},
  # ... more few-shot pairs ...
  {"role": "user", "content": "..."},  # or multimodal list
  {"role": "assistant", "content": "..."},
]
```

- **Multimodal user messages:** When images are present, `content` is a list: `[{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "data:image/..."}}]`.
- **Session lifecycle:** Created on first `/chat` with `session_id`; cleared via POST `/clear`. Sessions are in-memory; no persistence (Cloud Run instances are stateless).

### Multimodal support

- **Frontend:** Images added via file picker (+ button) or paste (Ctrl+V). Converted to base64 data URLs; max 5 images, 4MB each.
- **Backend:** Validates `data:image/...` URLs; max ~6MB each (base64 overhead). Passes to LiteLLM in `image_url` format; Gemini supports vision natively.
- **Safety:** `_extract_text_from_content()` pulls text from multimodal content so the user message can be checked for distress/medical keywords.

### Safety backstop

`safety.py` implements a two-stage check:

1. **Distress/crisis:** Keywords (e.g. suicide, self-harm, 988) and regex patterns. If detected in user or generation → returns crisis-resources fallback (988, Crisis Text Line).
2. **Medical emergency:** Keywords (e.g. chest pain, stroke, call 911) and regex patterns. If detected → returns medical-emergency fallback (911, ER, doctor).

`SafetyResult` includes `response`, `triggered`, `source` (user/generation), and `trigger_type`. The frontend shows a visual indicator when `safety_triggered` is true.

### Prompt engineering

Prompt structure in `prompt.py`:

1. **Role persona:** Vintage Coach expert; audience: owners and shoppers.
2. **Rules:** Hard-coded facts from PDF (serial/style numbers, era, hardware, damage inspection, care).
3. **In-scope:** Four areas: serial/style, era, damage inspection, care.
4. **Out-of-scope:** Redirects for market valuation, medical, final authentication; with canned phrases.
5. **Escape hatch:** Four uncertainty patterns (missing info, needs visual, unclear question, no evidence).
6. **Few-shot:** Six user/assistant pairs covering in-scope, out-of-scope, and edge cases.

### Frontend design

- **Query box:** Single textarea with + button (top-left); tooltip "Add images"; images preview inline above text.
- **Chat pane:** User messages show images first, then text below; assistant messages render Markdown (marked + DOMPurify).
- **State:** `sessionId`, `pendingImages`; no localStorage (session persistence was removed for Cloud Run compatibility).

### Deployment architecture

- **Dockerfile:** Python 3.12 slim; uv for package install; copies source; exposes 8080; runs `uvicorn main:app`.
- **Cloud Run:** Stateless; no session persistence across instances. Health check at `/health`.
- **Credential flow:** Application Default Credentials; Cloud Run service account needs `roles/aiplatform.user` for Vertex AI.


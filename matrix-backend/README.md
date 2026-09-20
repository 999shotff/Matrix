# Matrix — Question Paper Maker · Backend

FastAPI service that powers the generation flow shown in the prototype UI:
Source → Pattern → Teacher Behaviour (optional) → PYQs (optional) → Generate.

## What's here

```
app/
  main.py                 FastAPI app + CORS
  models.py                All request/response schemas
  routers/
    uploads.py              POST /api/uploads          — file upload (used by all 3 upload steps)
    settings.py             POST /api/settings/test     — verify a NIM/OpenAI-compatible endpoint
    generate.py              POST /api/generate         — the main pipeline
                              GET  /api/papers/{id}      — download the generated PDF
  services/
    ai_client.py             OpenAI-SDK wrapper — works with NVIDIA NIM, a self-hosted
                              MatrAIx-Persona-8B (vLLM/TGI), or any OpenAI-compatible server
    prompt_builder.py         Assembles the system + user prompt from the 4 UI inputs
    file_service.py           Saves uploads, extracts text (PDF/DOCX/TXT; images stubbed)
    pdf_generator.py          Renders the model's structured JSON into a downloadable PDF
```

## Run it

```bash
cd matrix-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in AI_BASE_URL / AI_API_KEY / AI_MODEL
uvicorn app.main:app --reload --port 8080
```

Open `http://localhost:8080/docs` for interactive Swagger docs — you can try every
endpoint from there without touching the frontend yet.

## Connecting MatrAIx-Persona-8B

This backend talks to models purely over the OpenAI-compatible `/chat/completions`
wire format, so no code changes are needed between providers — only `.env` (or the
Settings modal in the UI, which is sent per-request as `model_settings`) changes:

- **NVIDIA NIM (hosted)**: `AI_BASE_URL=https://integrate.api.nvidia.com/v1`, your NIM
  API key, `AI_MODEL=matraix/persona-8b` (confirm the exact catalog name on build.nvidia.com).
- **Self-hosted MatrAIx-Persona-8B**: pull `MatrAIx-ai/MatrAIx-Persona-8B` from
  GitHub, serve it behind vLLM or NVIDIA NIM's container (`nim deploy` / `vllm serve`),
  then point `AI_BASE_URL` at that server's `/v1` endpoint.
- **Anything else OpenAI-compatible** (OpenRouter, local Ollama with the OpenAI shim,
  etc.) works the same way.

## How a generate request flows

1. Frontend uploads files as they're added (`POST /api/uploads`) and collects the
   returned `file_id`s.
2. On "Generate", frontend calls `POST /api/generate` with all four steps' data plus
   (optionally) the user's saved model settings.
3. Backend extracts text from every uploaded file, builds one prompt (see
   `prompt_builder.py` for the exact rules — source grounding, no verbatim PYQ
   copying, the "never below Class 9 difficulty" floor, optional teacher-behaviour
   bias), and calls the model with JSON-mode.
4. The model's structured JSON is validated into a `QuestionPaper`, rendered to PDF,
   and both the structured paper (for the on-screen stats/curve) and a `pdf_url` are
   returned in one response.

## Known placeholders to finish before production

- **Web search** (`Source → Search the web` tab): `generate.py` currently inserts a
  placeholder string instead of real fetched content. Wire in a real search + fetch
  step (e.g. an existing web-search API) and pass the fetched page text into
  `extract_text_many`-style handling.
- **OCR for uploaded images**: `file_service.py` currently returns a stub note instead
  of real extracted text for `.png/.jpg`. Route these through an OCR or vision-language
  model (a NIM vision model works well here) before passing to the prompt.
- **Session persistence**: `session_id` is accepted throughout but nothing is
  persisted server-side yet — sessions currently live in the frontend (as agreed, this
  comes before real auth). Add a database once auth is in place.
- **Streaming progress**: the UI's "Reading source… Matching pattern… Drafting…" log is
  currently a fixed animation on the frontend. If you want it to reflect real backend
  progress, switch `/api/generate` to a streaming response (SSE) and emit a stage event
  per pipeline step.

# BID-PILOT AI — Local MVP

A local-first prototype for turning an RFP into an editable proposal draft. It includes a dark React dashboard, a FastAPI service, SQLite persistence, requirement review, company and knowledge context, templates, reviewer assignment, comments, and DOCX/PDF export. Demo mode works without an LLM key.

## Architecture

The code is separated into the frontend, API, local persistence, and draft/extraction services:

1. **Input:** React upload accepts PDF, DOCX, TXT, and Markdown files (25 MB limit).
2. **OCR & parsing:** PyMuPDF extracts PDF text and python-docx extracts DOCX text. For image-only PDFs, the parser attempts local Tesseract OCR; install the Tesseract executable separately and set `TESSERACT_CMD` when it is not on `PATH`.
3. **NLP:** local rule-based extraction classifies requirement wording as mandatory or optional.
4. **Multi-agent workflow:** a LangGraph graph runs Extraction, Analysis, Drafting, Cost Estimation, Compliance, and Optimisation nodes. Each saved proposal records the node run summary and mock/LLM mode.
5. **Template engine:** user-defined section outlines shape generated drafts.
6. **Validation:** edit requirement responses and review states; assign a reviewer, set workflow status, and add comments.
7. **Output:** edit and save proposals in SQLite, then export DOCX or PDF.

The knowledge base and company profile are persisted locally. A replaceable `KnowledgeRetriever` interface ranks entries using local TF-IDF/cosine similarity. Draft generation uses deterministic mock mode by default; configure `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` to use an OpenAI-compatible chat-completions API. Connection errors fall back to the local draft. Retrieval is lexical rather than embedding-based vector search. SQLite can be replaced behind the storage module in a later phase.

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer

## Backend setup (Windows PowerShell)

Open PowerShell in the project folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; interactive API docs are at `http://127.0.0.1:8000/docs`; health is `http://127.0.0.1:8000/api/health`.

## Frontend setup

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal, usually `http://localhost:5173`.

## Environment variables

Copy `.env.example` to `backend/.env` to configure the backend. `DATABASE_PATH` defaults to `./bidpilot.db` relative to the backend working directory. `FRONTEND_ORIGIN` configures CORS. Frontend `VITE_API_URL` may be set in `frontend/.env.local`; its default is `http://127.0.0.1:8000`. No API keys are needed or stored. To enable the optional single-admin login, set `AUTH_ENABLED=true`, choose a private `ADMIN_PASSWORD`, and set a long random `SESSION_SECRET` in `backend/.env`; then restart the backend. Do not commit that file. The login produces an eight-hour signed bearer token. This does not create individual reviewer accounts.

## Tests and build

From `backend` with its virtual environment active:

```powershell
python -m pytest
```

From `frontend`:

```powershell
npm run build
```

## Current scope and next phases

This is a local MVP for exploring the workflow. Optional single-admin authentication and read-only viewer token enforcement are included, but it is not a production multi-user system: team roles are assignment labels, not individual authenticated accounts; database migrations, audit/version history, embedding-based vector retrieval, hardened document security, and end-to-end tests remain future work. Before production, add user-managed accounts/roles, durable migrations/backups, file scanning/retention controls, observability, and deployment safeguards.

Suggested phases:

1. Run and verify the local MVP, review generated requirements, and edit/save/export proposals.
2. Add extraction confidence/evidence review and test OCR against representative scans.
3. Add embedding-based retrieval behind the existing retriever interface.
4. Add authenticated users, authorization, version/audit history, and production deployment controls.

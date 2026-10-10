# BID-PILOT AI — Local MVP

A local-first prototype for turning an RFP into an editable proposal draft. It includes a dark React dashboard, a FastAPI service, SQLite or PostgreSQL-ready persistence, requirement review, company and knowledge context, templates, reviewer assignment, comments, and DOCX/PDF export. Demo mode works without an LLM key.

## Architecture

The code is separated into the frontend, API, local persistence, and draft/extraction services:

1. **Input:** React upload accepts PDF, DOCX, TXT, and Markdown files (25 MB limit).
2. **OCR & parsing:** PyMuPDF extracts PDF text and python-docx extracts DOCX text. For image-only PDFs, the parser attempts local Tesseract OCR; install the Tesseract executable separately and set `TESSERACT_CMD` when it is not on `PATH`.
3. **NLP:** local rule-based extraction classifies requirement wording as mandatory or optional.
4. **Multi-agent workflow:** a LangGraph graph runs Extraction, Analysis, Drafting, Cost Estimation, Compliance, and Optimisation nodes. Each saved proposal records the node run summary and mock/LLM mode.
5. **Template engine:** user-defined section outlines shape generated drafts.
6. **Validation:** edit requirement responses and review states; assign a reviewer, set workflow status, and add comments.
7. **Output:** edit and save proposals in the configured database, then export DOCX or PDF.

The knowledge base and company profile are persisted locally. A replaceable `KnowledgeRetriever` interface ranks entries using local TF-IDF/cosine similarity. Draft generation uses deterministic mock mode by default; configure `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` to use an OpenAI-compatible chat-completions API. Connection errors fall back to the local draft. Retrieval is lexical rather than embedding-based vector search. The SQLAlchemy storage adapter supports SQLite and PostgreSQL through the optional `DATABASE_URL` setting. Alembic applies forward-only, versioned schema migrations on backend startup and can also be run manually from `backend` with `python -m alembic upgrade head`.

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

Copy `.env.example` to `backend/.env` to configure the backend. `DATABASE_PATH` defaults to `./bidpilot.db` relative to the backend working directory; set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL to use PostgreSQL instead. `FRONTEND_ORIGIN` configures CORS. Frontend `VITE_API_URL` may be set in `frontend/.env.local`; its default is `http://127.0.0.1:8000`. No API keys are needed or stored in the repository. To enable authentication, set `AUTH_ENABLED=true`, choose a private `ADMIN_PASSWORD`, and set a long random `SESSION_SECRET` in `backend/.env`; then restart the backend. Do not commit that file. The admin login produces an eight-hour signed bearer token and can manage individual Reviewer and Viewer accounts.

## Production security configuration

For a production deployment, set `APP_ENV=production`. The backend will refuse to start unless authentication is enabled, the admin password is at least 16 characters, the session secret is at least 32 characters, the frontend origin uses HTTPS, and ClamAV scanning is enabled. Set these values only in the deployment's secret manager or private environment; never commit credentials.

Configure `CLAMAV_ENABLED=true`, `CLAMAV_HOST`, and `CLAMAV_PORT` to point at a private, reachable ClamAV daemon. Uploads are rejected if the scanner is unavailable or cannot verify the file. Local demo mode keeps scanning disabled by default.

## Tests and build

From `backend` with its virtual environment active:

```powershell
python -m pytest
```

From `frontend`:

```powershell
npm run build
```

## Current scope and production gaps

The MVP includes optional signed authentication with individual reviewer/viewer accounts, role checks, proposal version snapshots and audit events, and a SQLAlchemy storage adapter configured for SQLite or PostgreSQL. The upload path validates supported file types and size, checks PDF/DOCX structure, applies parsing limits, and can scan through ClamAV. Production mode refuses to start unless authentication, strong secrets, HTTPS frontend origin, and ClamAV scanning are configured. A ClamAV service, encrypted storage, retention/deletion policies, scheduled backups, monitoring, and a deployment security review are still required before handling customer RFPs.

Recommended next phases:

1. Run backend tests and frontend build after upload hardening; test representative PDF, DOCX, oversized, malformed, and scanned files.
2. Schedule and periodically restore-test database backups (SQLite backup API or PostgreSQL `pg_dump`/`pg_restore`).
3. Add evidence citations and confidence review, then improve retrieval with embeddings and quality evaluation.
4. Configure a reachable ClamAV daemon, encrypted storage, retention/deletion controls, observability, and deployment safeguards before using real customer RFPs.


## Database migrations and backups

The backend applies versioned Alembic migrations at startup. To apply them manually from the `backend` directory, run:

```powershell
python -m alembic upgrade head
```

For SQLite, stop the backend before copying the database file for a simple backup. For a consistent online backup, use Python's SQLite backup API:

```powershell
python -c "import sqlite3; src=sqlite3.connect('bidpilot.db'); dst=sqlite3.connect('bidpilot-backup.db'); src.backup(dst); dst.close(); src.close()"
```

For PostgreSQL, install the PostgreSQL client tools and use a native libpq connection URL in `PGDATABASE_URL`:

```powershell
pg_dump --format=custom --file=bidpilot.dump $env:PGDATABASE_URL
pg_restore --clean --if-exists --dbname=$env:PGDATABASE_URL bidpilot.dump
```

Keep backup files encrypted and restrict access. Test restores regularly; a backup is useful only if it can be restored.

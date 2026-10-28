# BID-PILOT AI — RFP-to-Proposal Workflow MVP

A **local-first prototype** that helps teams turn Request for Proposal (RFP) documents into editable proposal drafts. Bid-Pilot combines a React dashboard with a FastAPI backend, document extraction, requirement review, configurable templates, reviewer workflows, and DOCX/PDF export.

> **Project status:** MVP / local development prototype. It is not presented as a production-ready service. Review generated content for accuracy, completeness, compliance, and pricing before using it externally.

## Contents

- [What it does](#what-it-does)
- [Key capabilities](#key-capabilities)
- [How it works](#how-it-works)
- [Technology stack](#technology-stack)
- [Requirements](#requirements)
- [Run locally on Windows](#run-locally-on-windows)
- [Run locally on macOS or Linux](#run-locally-on-macos-or-linux)
- [Configuration](#configuration)
- [Optional OCR and LLM configuration](#optional-ocr-and-llm-configuration)
- [Tests and production build](#tests-and-production-build)
- [Security notes and known limitations](#security-notes-and-known-limitations)
- [Roadmap](#roadmap)

## What it does

Bid-Pilot provides a workflow for extracting requirements from an RFP and preparing a draft proposal that people can edit and review. It is designed to demonstrate document-processing, API, workflow, and full-stack application concepts in one project.

## Key capabilities

- **Document intake:** accepts PDF, DOCX, TXT, and Markdown files; the application enforces an upload size limit.
- **Text extraction:** uses PyMuPDF for PDF text and python-docx for DOCX files. Scanned PDFs can use local Tesseract OCR when configured.
- **Requirement extraction:** rule-based logic classifies requirement wording as mandatory or optional.
- **Draft workflow:** LangGraph coordinates extraction, analysis, drafting, cost-estimation, compliance, and optimisation steps.
- **Editable proposal content:** review and update requirement responses and proposal sections.
- **Reusable context:** maintain company profile information, knowledge-base entries, and proposal templates.
- **Team review:** assign reviewers, add comments, update workflow status, and use reviewer/viewer roles when authentication is enabled.
- **Export:** generate editable DOCX and PDF outputs.
- **Local persistence:** SQLite is the default; PostgreSQL can be configured with a database URL.
- **Demo mode:** a deterministic local draft mode is available without an LLM API key.

## How it works

1. Upload an RFP document.
2. Extract text from the document; scanned PDFs may require OCR setup.
3. Identify and classify requirement statements.
4. Run the proposal workflow to create a draft and record workflow summaries.
5. Review and edit the proposal, assign reviewers, and add comments.
6. Export the reviewed draft to DOCX or PDF.

### Architecture at a glance

```text
React + Vite frontend
        |
        | HTTP / REST
        v
FastAPI backend
        |
        +--> PDF / DOCX / TXT / Markdown parsing
        +--> Requirement extraction
        +--> LangGraph proposal workflow
        +--> Company profile, knowledge base, templates
        +--> SQLAlchemy persistence (SQLite / PostgreSQL)
        +--> DOCX / PDF export
```

The knowledge retriever currently uses local TF-IDF/cosine similarity. It is lexical retrieval, **not embedding-based semantic vector search**. LLM-backed drafting is optional and uses an OpenAI-compatible chat-completions API when configured.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| API | Python, FastAPI, Uvicorn |
| Workflow | LangGraph |
| Document processing | PyMuPDF, python-docx, Pillow, optional Tesseract OCR |
| Persistence | SQLAlchemy, SQLite, optional PostgreSQL |
| Migrations | Alembic |
| Export | python-docx, ReportLab |
| Tests | pytest, HTTPX |

## Requirements

- **Python 3.11 or newer**
- **Node.js 20 or newer** (includes npm)
- Git
- Optional: Tesseract OCR for scanned/image-only PDFs
- Optional: PostgreSQL for a non-SQLite database
- Optional: a reachable ClamAV daemon for configured upload scanning

## Run locally on Windows

Run commands from PowerShell. First clone the repository and enter the project directory:

```powershell
git clone https://github.com/sahilkumar21072004-a11y/Bid-Pilot_AI-MVP.git
cd Bid-Pilot_AI-MVP
```

### 1. Configure and start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload
```

The first run initializes the configured database. Once the server starts, open:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/api/health

Keep this terminal running.

### 2. Start the frontend

Open a **second** PowerShell terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually http://localhost:5173.

### PowerShell note

If PowerShell blocks virtual-environment activation due to its execution policy, use a permitted local development setup or activate the environment from Command Prompt with:

```bat
.venv\Scripts\activate.bat
```

## Run locally on macOS or Linux

From the repository root, configure the backend:

```bash
git clone https://github.com/sahilkumar21072004-a11y/Bid-Pilot_AI-MVP.git
cd Bid-Pilot_AI-MVP/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp ../.env.example .env
python -m uvicorn app.main:app --reload
```

In a second terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Use the local URL printed by Vite. These instructions describe the expected setup; environment-specific dependencies may require additional configuration.

## Configuration

The repository includes a safe example configuration at `.env.example`. For local development, the Windows and macOS/Linux instructions copy it to `backend/.env`.

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application display name |
| `APP_ENV` | Environment mode; use `production` only with production security settings configured |
| `DATABASE_PATH` | Local SQLite database path; defaults to `./bidpilot.db` relative to the backend working directory |
| `DATABASE_URL` | Optional SQLAlchemy database URL; takes precedence over `DATABASE_PATH` when set |
| `FRONTEND_ORIGIN` | Allowed frontend origin for CORS |
| `DEMO_MODE` | Enables local demo behaviour |
| `LLM_API_KEY` | Optional secret for an OpenAI-compatible chat-completions API |
| `LLM_BASE_URL` | Optional LLM API base URL |
| `LLM_MODEL` | Optional model identifier |
| `TESSERACT_CMD` | Optional full path to the Tesseract executable |
| `AUTH_ENABLED` | Enables workspace authentication |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Admin login configuration when authentication is enabled |
| `SESSION_SECRET` | Secret used for signed session tokens |
| `CLAMAV_ENABLED`, `CLAMAV_HOST`, `CLAMAV_PORT` | Optional upload-scanning service configuration |
| `VITE_API_URL` | Frontend API URL; defaults to `http://127.0.0.1:8000` |

Keep secrets in your private local environment or deployment secret manager. **Never commit `backend/.env`, passwords, API keys, or real customer RFP documents.** The repository's `.gitignore` excludes common virtual environments, local environment files, databases, and Python cache files.

### Optional PostgreSQL

Set `DATABASE_URL` to a valid SQLAlchemy PostgreSQL URL and ensure the database is reachable. Example format:

```text
postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME
```

Use your own credentials; do not commit the connection string.

## Optional OCR and LLM configuration

### Scanned PDF OCR

The application can attempt local Tesseract OCR for image-only PDFs. Install the Tesseract executable separately and set `TESSERACT_CMD` to its full path if it is not available on `PATH`. OCR may require additional time and resources; verify extracted text before relying on it.

### LLM-backed drafting

Demo mode can work without an LLM key. To use an OpenAI-compatible chat-completions endpoint, configure `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in the private backend environment, then restart the backend. Keep the key private. The application has a local fallback path when the configured LLM connection fails; check the UI and backend logs to understand which mode was used for a draft.

## Tests and production build

These commands are provided for you to run locally; **tests and build have not been verified as part of this README update**.

Backend tests (from the `backend` directory, with the virtual environment active):

```powershell
python -m pytest
```

Frontend production build (from the `frontend` directory):

```powershell
npm run build
```

You can also apply database migrations manually from the `backend` directory:

```powershell
python -m alembic upgrade head
```

Review command output and resolve any environment-specific errors before describing the project as verified.

## Security notes and known limitations

- Treat this as an MVP/local prototype, not a production-ready service for confidential customer documents.
- Generated proposal content can be incomplete or incorrect. Human review is required for requirements, compliance statements, prices, and contractual commitments.
- Requirement classification uses rule-based logic and can misclassify ambiguous wording.
- Retrieval uses TF-IDF/cosine similarity rather than embeddings.
- Scanned-document OCR depends on an external Tesseract installation.
- Production mode is designed to require authentication, a strong admin password, a strong session secret, an HTTPS frontend origin, and configured ClamAV scanning. Upload scanning fails closed when the scanner is required but unavailable.
- Before processing real customer RFPs, add and verify encrypted storage, retention and deletion policies, access controls, backups and restore procedures, monitoring, and a deployment security review.
- Do not upload real confidential documents, personal data, credentials, or secrets to a public repository or demo environment.

## Roadmap

- [ ] Run backend tests and frontend build; document the verified results.
- [ ] Test normal, malformed, oversized, and scanned PDF/DOCX uploads.
- [ ] Add evidence citations and confidence indicators for extracted requirements.
- [ ] Evaluate requirement extraction and draft quality on representative, permissioned sample documents.
- [ ] Improve retrieval and measure quality before adopting embedding-based search.
- [ ] Configure encrypted storage, retention/deletion controls, backups, monitoring, and production security review.

## License

No license is declared in this README. Add a `LICENSE` file before explicitly granting reuse rights.

# Primordial

> **Open-Source Decision Intelligence and Knowledge Recovery System**  
> Problem Statement 06 — Hacktoberfest 2026 | Hack Day Sonipat  
> **Team:** Shaurya Negi, Prince Chhikara, Manisha Jain

---

## Overview

Primordial is an open-source, local-first platform that extracts, verifies, and compiles historical architectural decisions from complex GitHub discussions (Issues, Pull Requests, Code Reviews) into verifiable Architectural Decision Records ([MADR 3.0.0](https://adr.github.io/madr/)).

### Implementation Roadmap
1. **Module 1: Project Setup and Backend Foundation** *(Completed)*
2. **Module 2: GitHub Integration** *(Completed)*
3. **Module 3: Data Preprocessing** *(Completed)*
4. **Module 4: AI Decision Detection** *(Completed)*
5. **Module 5: Rationale and Evidence Extraction** *(Completed)*
6. **Module 6: Evidence Verification** *(Completed)*
7. **Module 7: ADR/MADR Generation** *(Completed)*
8. **Module 8: Storage and Search** *(Completed)*
9. **Module 9: Historical PR Radar** *(Completed)*
10. **Module 10: Frontend Development** *(Completed)*
11. **Module 11: Integration and Testing**

---

## Module 1 Architecture & Structure

```text
primordial-hacktoberfest/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application & lifecycle
│   │   ├── cli.py                  # Phase 1 CLI executable entrypoint
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Top-level API router (/api/v1)
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       └── health.py       # GET /api/v1/health
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic BaseSettings & .env loader
│   │   │   ├── exceptions.py       # Custom exception hierarchy
│   │   │   └── logging.py          # Structured logging configuration
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py          # Canonical Pydantic domain models
│   │   │   └── entities.py         # Internal dataclasses & Enums
│   │   ├── github/                 # GitHub REST API client (Module 2)
│   │   ├── preprocessing/          # Noise cleaner & context budgeter (Module 3)
│   │   ├── ai/                     # Local Ollama AI integration (Modules 4 & 5)
│   │   ├── adr/                    # MADR 3.0.0 Markdown compiler (Module 6)
│   │   │   └── templates/
│   │   │       └── madr_template.md# MADR 3.0.0 Jinja2 template
│   │   ├── storage/                # SQLite WAL & FTS5 search (Module 7)
│   │   └── services/               # Pipeline orchestration service (Module 7)
│   ├── requirements.txt            # Pinned dependencies
│   ├── .env.example                # Template environment variables
│   └── pytest.ini                  # Backend Pytest configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared pytest fixtures & async HTTP test client
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py          # Settings and environment overrides
│   │   ├── test_exceptions.py      # Custom exception hierarchy verification
│   │   └── test_schemas.py         # Pydantic models & validation rules
│   └── integration/
│       ├── __init__.py
│       └── test_health_api.py      # Health endpoint, route mount & error handling
├── .env.example                    # Root template environment variables
├── .gitignore                      # Git ignore rules for virtualenvs, caches & secrets
├── pytest.ini                      # Root Pytest configuration
└── README.md                       # Project overview and setup instructions
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Checkout Branch
```bash
git clone https://github.com/princechhikara/primordial-hacktoberfest.git
cd primordial-hacktoberfest
git checkout feature/backend-foundation
```

### 2. Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables
```bash
cp backend/.env.example backend/.env
# Optional: also copy to root if running commands from repository root
cp .env.example .env
```

---

## Running the Backend

Start the FastAPI development server with Uvicorn:

```bash
# From repository root:
python -m uvicorn app.main:app --app-dir backend --reload --port 8000

# Or navigate to backend:
cd backend
uvicorn app.main:app --reload --port 8000
```

Once running:
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Service Metadata:** [http://localhost:8000/](http://localhost:8000/)
- **Health Check Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Example Health Check Response (`GET /api/v1/health`)
```json
{
  "status": "ok",
  "app": "Primordial",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "ok",
    "details": "WAL mode: True",
    "url": null
  },
  "ollama": {
    "status": "unreachable",
    "details": "Ollama offline at http://localhost:11434",
    "url": "http://localhost:11434"
  }
}
```

---

## Running Automated Tests

Run the full automated test suite using `pytest`:

```bash
# From repository root:
pytest

# Or with verbose output:
pytest -v

# Or from the backend directory:
cd backend
pytest
```

---

## Error Handling Specifications

All errors adhere to consistent, structured JSON responses:

| Status Code | Error Code | Description |
|---|---|---|
| `400 Bad Request` | `INVALID_GITHUB_URL` | Malformed GitHub issue/PR URL syntax |
| `404 Not Found` | `GITHUB_RESOURCE_NOT_FOUND` / `HTTP_404` | Nonexistent endpoint or GitHub resource |
| `405 Method Not Allowed` | `HTTP_405` | Unsupported HTTP method |
| `422 Unprocessable Entity` | `EMPTY_DISCUSSION` / `VALIDATION_ERROR` / `SCHEMA_VALIDATION_ERROR` | Empty discussion or invalid payload/schema |
| `429 Too Many Requests` | `GITHUB_RATE_LIMIT_EXCEEDED` | GitHub API rate limit reached |
| `502 Bad Gateway` | `AI_MODEL_RESPONSE_ERROR` | Ollama returned error response or malformed JSON |
| `503 Service Unavailable` | `AI_SERVICE_UNAVAILABLE` | Local Ollama daemon offline or unreachable |
| `504 Gateway Timeout` | `AI_MODEL_TIMEOUT` | AI model inference request timed out |

---

## CLI Execution

Primordial includes a command-line interface for running pipeline stages directly:

```bash
# Set PYTHONPATH
export PYTHONPATH=backend

# 1. Fetch & normalize raw GitHub Issue / PR discussion (Module 2)
python -m app.cli fetch https://github.com/nodejs/node/pull/41749

# 2. Preprocess, filter noise/bots, and format context transcript (Module 3)
python -m app.cli preprocess https://github.com/nodejs/node/pull/41749 --transcript transcript.txt

# 3. Detect candidate engineering decisions using local Ollama model (Module 4)
python -m app.cli detect https://github.com/nodejs/node/pull/41749 --model qwen2.5:7b --output decisions.json

# 4. Extract rationale, arguments, trade-offs, and alternatives (Module 5)
python -m app.cli extract-rationale https://github.com/nodejs/node/pull/41749 \
  --model qwen2.5:7b --output rationale.json

# 5. Verify evidence grounding and authentic comment provenance (Module 7)
python -m app.cli verify-evidence https://github.com/nodejs/node/pull/41749 \
  --output verification.json

# 6. Generate MADR 3.0.0 Architecture Decision Records (Module 8)
python -m app.cli generate-adr https://github.com/nodejs/node/pull/41749 \
  --output ADR-41749.md --format markdown

# 7. Search historical engineering decisions (Module 9)
python -m app.cli search "Undici fetch"

# 8. List all recorded decisions in knowledge store (Module 9)
python -m app.cli list-decisions --repo nodejs/node

# 9. Inspect specific decision details with full claim evidence (Module 9)
python -m app.cli show-decision dec-41749-1

# 10. Run Historical PR Radar against a Pull Request (Module 10)
python -m app.cli radar https://github.com/nodejs/node/pull/50001 --threshold 0.5
```

### Historical PR Radar API
Analyze incoming Pull Requests programmatically via FastAPI:
```bash
curl -X POST http://localhost:8000/api/radar/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/nodejs/node/pull/50001", "threshold": 0.5}'
```

The `extract-rationale` command runs the full pipeline (fetch → preprocess → detect → extract) and outputs a JSON document with the following top-level structure:

```json
{
  "is_rationale_extracted": true,
  "repository": "nodejs/node",
  "entity_number": 41749,
  "resource_type": "pull_request",
  "source_url": "https://github.com/nodejs/node/pull/41749",
  "model_name": "qwen2.5:7b",
  "decisions_evaluated": 2,
  "rationales": [
    {
      "decision_id": "dec-41749-1",
      "decision_summary": "...",
      "status": "accepted",
      "rationale": { "statement": "...", "supporting_comment_ids": [...], "evidence_status": "verified", ... },
      "supporting_arguments": [...],
      "opposing_arguments": [...],
      "rejected_alternatives": [...],
      "trade_offs": [...],
      "consequences": [...],
      "evidence_comment_ids": ["101", "204"],
      "confidence": 0.88,
      "extraction_notes": [...]
    }
  ],
  "total_evidence_citations": 5,
  "processing_notes": [...]
}
```

All extracted claims cite real comment IDs from the original discussion. Fields without grounded evidence are explicitly marked `"evidence_status": "insufficient_evidence"` rather than silently omitted or invented.

### Ollama Model Setup for Decision Detection
To run local decision detection:
```bash
# 1. Install & start Ollama
ollama serve

# 2. Pull the primary open-weight model
ollama pull qwen2.5:7b
```

---

## Frontend Development Dashboard

Primordial includes a React + Vite + Tailwind CSS developer dashboard with dark charcoal theme.

### Frontend Setup
```bash
cd frontend
npm install
```

### Running the Frontend Dev Server
```bash
# Start the backend first (from repo root):
cd backend && uvicorn app.main:app --reload --port 8000

# Then start the frontend (from frontend/):
cd frontend && npm run dev
```

The frontend dev server runs on **http://localhost:5173** and proxies `/api` requests to the backend on port 8000.

### Frontend Pages
| Page | Route | Description |
|---|---|---|
| Dashboard | `/` | Overview with stats cards and recent activity |
| Analyze | `/analyze` | Run full pipeline on a GitHub URL |
| Decisions | `/decisions` | Browse and filter all recovered decisions |
| Decision Detail | `/decisions/:id` | Full decision view with rationale and evidence |
| ADR Library | `/adrs` | Browse generated ADRs |
| Search | `/search` | Full-text search across decisions |
| PR Radar | `/radar` | Analyze PRs against historical decisions |
| Settings | `/settings` | Backend health and API reference |

### Production Build
```bash
cd frontend
npm run build    # outputs to frontend/dist/
```



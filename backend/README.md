# Primordial Backend

FastAPI backend service and core pipeline for Primordial.

## Quickstart

```bash
# 1. Activate virtual environment
source ../.venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env

# 4. Start local development server
uvicorn app.main:app --reload --port 8000

# 5. Run tests
pytest
```

## Endpoints

- `GET /` — Service metadata
- `GET /api/v1/health` — Service and dependency health status
- `POST /api/v1/extract` — Synchronous decision extraction (Phase 2)
- `GET /api/v1/decisions` — Search and listing of recovered decisions (Phase 2)


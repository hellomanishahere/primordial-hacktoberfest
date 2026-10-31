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

## CLI Commands

Primordial provides an integrated CLI for testing pipeline components:

```bash
export PYTHONPATH=.

# Ingest and normalize GitHub discussion
python -m app.cli fetch https://github.com/nodejs/node/pull/41749

# Preprocess and prepare context transcript
python -m app.cli preprocess https://github.com/nodejs/node/pull/41749 -o cleaned.json -t transcript.txt

# Run AI decision detection (Ollama qwen2.5:7b)
python -m app.cli detect https://github.com/nodejs/node/pull/41749 -m qwen2.5:7b -o decisions.json
```

## Endpoints

- `GET /` — Service metadata
- `GET /api/v1/health` — Service and dependency health status
- `POST /api/v1/extract` — Synchronous decision extraction (Phase 2)
- `GET /api/v1/decisions` — Search and listing of recovered decisions (Phase 2)

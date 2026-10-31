# Primordial

**Open Source Decision Intelligence and Knowledge Recovery**

Primordial recovers engineering decisions, rejected alternatives, and their reasoning from public GitHub and Discourse discussions. It stores decision records with references back to source comments, generates MADR Markdown, and can compare proposed changes with recorded decisions.

## Current implementation

- GitHub issue and pull request ingestion, including comments and pull request review comments.
- Discourse topic ingestion.
- A three-stage extraction pipeline, evidence checking, MADR generation, and SQLite storage.
- A web dashboard for source exploration, decision review, radar scans, and curated benchmark fixtures.
- A local Ollama adapter for `llama3.2:3b`, `phi3.5:latest`, and `qwen2.5-coder:7b`.
- A deterministic heuristic fallback when Ollama is unavailable. This fallback is application code, not an AI model.

The built-in discussions are curated fixtures for development and demos. A fixture result does not demonstrate extraction quality on unseen discussions. The benchmark is a small fixture check, not an independent accuracy evaluation.

## Requirements

- Python 3.10 or later.
- Ollama and the three models above for model-backed inference. Ollama is optional for running the deterministic fallback.
- Internet access to fetch public GitHub or Discourse discussions. `GITHUB_TOKEN` is optional and can raise GitHub API rate limits.

## Install and run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
```

For model-backed inference, install and start [Ollama](https://ollama.com/), then pull the model tags used by the pipeline:

```bash
ollama pull llama3.2:3b
ollama pull phi3.5:latest
ollama pull qwen2.5-coder:7b
```

Start the application:

```bash
python -m primordial.server.app
```

Open <http://localhost:8080>. The health endpoint reports whether the server selected the Ollama or heuristic adapter: <http://localhost:8080/api/health>.

## Examples

[`examples/`](examples/) contains a representative curated discussion input and an actual pipeline output produced by the deterministic heuristic fallback. The output is labeled with its runtime mode so it is not mistaken for a model-generated result.

## Tests and benchmark

Run the unit and integration tests:

```bash
python -m unittest discover -s tests -v
```

Run the curated fixture benchmark:

```bash
python benchmarks/evaluate.py
```

Benchmark scores are fixture match rates only. The fixtures and heuristic fallback encode expected scenarios, so these scores should not be presented as general accuracy or as independent model evaluation.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Server and inference adapter status |
| `GET` | `/api/samples` | List bundled discussion fixtures |
| `POST` | `/api/discussions/fetch` | Fetch a discussion or load an exact fixture |
| `POST` | `/api/pipeline/run` | Run decision extraction for a stored discussion |
| `GET` | `/api/decisions` | Search saved decisions |
| `GET` | `/api/decisions/{id}` | Retrieve a saved decision |
| `POST` | `/api/radar/scan` | Compare a proposed change with saved decisions |
| `GET` | `/api/benchmark/evaluate` | Run the curated fixture benchmark |

## Project structure

```text
primordial/       Python application package
  ai/             Ollama and heuristic inference adapters and pipeline
  connectors/     GitHub, Discourse, and curated discussion fixtures
  frontend/       Dashboard served by the Python server
  storage/        SQLite persistence layer
  verification/   Evidence quote checks
tests/            Unit and integration tests
benchmarks/       Curated fixture benchmark
examples/         Sample input and actual application output
HACKATHON.md      Team, problem statement, and model disclosure
```

## License

MIT. See [`LICENSE`](LICENSE).

# Hacktoberfest 2026 — Project Submission

## Team

- **Team:** Primordial
- **Members:** Shaurya Negi, Prince Chhikara, Manisha Jain
- **Event:** Hack Day Sonipat, Newton School of Technology, Rishihood University

## Selected problem

**Problem 06: Open Source Decision Intelligence and Knowledge Recovery**

Important engineering decisions are often buried in issues, pull requests, review comments, and technical forums. Primordial is designed to recover accepted decisions, rejected alternatives, reasoning, and references to their original discussions. It also provides a decision library and a radar that compares proposed changes with saved decisions.

## Product implementation

The repository includes GitHub and Discourse connectors, a three-stage extraction pipeline, SQLite persistence, an evidence-checking layer, MADR generation, a web dashboard, and a historical decision radar. Bundled conversations are curated fixtures for development and demonstration; they are not live source data.

The connectors return an error when a live source cannot be fetched. They do not substitute an unrelated fixture or fabricate a discussion. An exact built-in sample can still be selected explicitly for a repeatable demonstration.

## Open-weight models and rationale

When Ollama is available with the required models installed, the application uses these local model tags:

| Stage | Model tag | Intended role |
|---|---|---|
| Discussion preprocessing | `llama3.2:3b` | Summarize context and identify discussion participants and topics |
| Argument mining | `phi3.5:latest` | Identify proposals, objections, and rejected alternatives |
| Decision synthesis | `qwen2.5-coder:7b` | Produce a structured decision record and MADR content |

The models were selected for the pipeline’s separate summarization, argument-mining, and structured-synthesis tasks. Model-backed operation requires a local Ollama service and all three model tags; the health endpoint reports the active adapter and installed models.

When Ollama is unavailable, the application can use a deterministic heuristic fallback. **That fallback is ordinary application code, not an AI model.** Fallback-generated examples or benchmark results must be labeled accordingly. The team must use the Ollama-backed mode when demonstrating model-driven core functionality.

## Evaluation status

The included benchmark checks a small set of curated fixtures against expected decision names, evidence flags, and radar scenarios. Because the heuristic fallback contains fixture-specific rules, benchmark scores are fixture match rates, not independent accuracy measurements or evidence of generalization to unseen discussions. The example output in `examples/` identifies the adapter mode that produced it.

## Run the application

From the repository root, install and start the project:

```bash
python -m pip install -e .
python -m primordial.server.app
```

Open <http://localhost:8080>. For Ollama-backed execution, install Ollama and pull the model tags listed above. Setup, test, and benchmark commands are documented in `README.md`.

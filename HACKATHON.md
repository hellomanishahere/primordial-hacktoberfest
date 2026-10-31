# Hacktoberfest 2026 – Project Submission

**Event:** Hacktoberfest 2026 | Hack Day Sonipat  
**Date:** 31 October 2026  
**Venue:** Newton School of Technology, Rishihood University, Sonipat  

---

## 1. Team Information

- **Team Name:** Primordial
- **Repository Name:** primordial-hacktoberfest
- **Team Members:**
  1. **Shaurya Negi**
  2. **Prince Chhikara**
  3. **Manisha Jain**

*(Note: GitHub usernames are pending registration/linking. In strict accordance with hackathon rules, no placeholder or speculative handles have been assigned.)*

---

## 2. Selected Problem Statement

### **Problem 06: Open Source Decision Intelligence and Knowledge Recovery**
- **Category:** Knowledge Management | Developer Intelligence | Information Retrieval
- **Track:** Hacktoberfest 2026 Official Engineering Challenge

### Problem Context & Objectives
Open-source software (OSS) repositories represent some of the most dynamic engineering ecosystems in the world. However, vital architectural and technical decisions—the *why* behind design trade-offs, rejected approaches, performance compromises, and structural pivots—frequently remain buried under hundreds of issue comments, fragmented pull request reviews, and disparate technical threads. When new contributors join or existing maintainers review new pull requests touching legacy subsystems, they often lack contextual visibility into historical debates, risking inadvertent regressions, re-proposing previously rejected designs, or repeating past architectural mistakes.

**Primordial** builds an end-to-end, reproducible, and verifiable **Open Source Decision Intelligence and Knowledge Recovery Platform** that:
1. Ingests public GitHub issues, pull requests, review comments, and threaded discussions.
2. Segments and cleans high-noise conversation data while retaining critical deliberation tokens.
3. Performs argument and rationale mining to contrast accepted solutions against discarded alternatives.
4. Synthesizes formal Architectural Decision Records (ADR / MADR compliant) with strict schema validation.
5. Grounds recovered decisions to concrete source code repositories and file paths with line-level or symbol-level references.
6. Preserves bidirectional traceability and cryptographic/URL permalinks back to original discussion comments as verifiable evidence.
7. Proactively surfaces historical decisions when new pull requests modify associated source files, computing impact scores and warning maintainers of potential design conflicts.

---

## 3. Multi-Model Open-Source AI Architecture & Technical Justification

To adhere strictly to Hacktoberfest requirements, our architecture avoids all paid or proprietary closed-source APIs. Instead, it employs a targeted, multi-stage open-source model pipeline where each model is mapped to its specialized cognitive domain:

```
                          ┌───────────────────────────────────────────────┐
                          │   Public GitHub Issue / Pull Request Thread   │
                          └──────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
               ┌─────────────────────────────────────────────────────────────────┐
               │ Stage 1: Thread Preprocessing & Noise Filtering                 │
               │ Model: Llama 3.2-3B-Instruct                                    │
               │ • Prunes boilerplate (CI logs, +1s, greetings, etiquette)       │
               │ • Summarizes multi-party conversational progression             │
               │ • Extracts core technical controversy/problem statement         │
               └─────────────────────────────────┬───────────────────────────────┘
                                                 │
                                                 ▼
               ┌─────────────────────────────────────────────────────────────────┐
               │ Stage 2: Argumentation Mining & Alternative Analysis            │
               │ Model: Phi-3.5-mini-instruct                                    │
               │ • Identifies alternative proposals (Plan A vs. Plan B vs. C)    │
               │ • Extracts pros, cons, failure modes, benchmarks, objections    │
               │ • Isolates reasons for rejection vs. consensus drivers          │
               └─────────────────────────────────┬───────────────────────────────┘
                                                 │
                                                 ▼
               ┌─────────────────────────────────────────────────────────────────┐
               │ Stage 3: Deliberation Synthesis & Code Grounding                │
               │ Model: Qwen 2.5-Coder-7B-Instruct                               │
               │ • Synthesizes standard MADR / JSON decision schemas             │
               │ • Grounds decisions against source tree diffs & file references │
               │ • Evaluates trade-offs, confidence scores, and affected modules │
               └─────────────────────────────────┬───────────────────────────────┘
                                                 │
                                                 ▼
                          ┌───────────────────────────────────────────────┐
                          │ Verified Decision Record & Historical PR Radar│
                          │ • Bidirectional permalinks to GitHub sources  │
                          │ • Code change conflict detection on PR reviews│
                          └───────────────────────────────────────────────┘
```

### Detailed Model Roles & Technical Justifications

| Stage | Model Name | Primary Responsibility | Technical Justification |
| :--- | :--- | :--- | :--- |
| **1** | **Llama 3.2-3B-Instruct** | Discussion Summarization & Thread Noise Filtering | Features an optimized 3-billion-parameter edge footprint with exceptional conversational understanding. Perfect for streaming tokenization over large comment threads, discarding conversational pleasantries and bot noise, while preserving nuanced developer intent. |
| **2** | **Phi-3.5-mini-instruct** | Argumentation Mining & Rejection Rationale Analysis | Exceptionally strong in formal logic, step-by-step reasoning, and argument extraction relative to its compact 3.8B size. Excels at identifying conflicting viewpoints, separating the *accepted* consensus from *rejected* alternatives, and cataloging the explicit technical reasons for discarding ideas. |
| **3** | **Qwen 2.5-Coder-7B-Instruct** | Deliberation Synthesis, Code-to-Decision Grounding & Structured JSON | Pre-trained extensively on source code, commit diffs, and structured syntax. Excels at producing deterministic, validated JSON and MADR formats without hallucinating code symbols. Maps abstract decisions directly to concrete file paths and syntactic definitions. |

### Inference Strategy & Model Portability
- **Zero Closed-Source APIs:** 100% compliant with the hackathon rule prohibiting paid commercial APIs.
- **Pluggable Execution Engine:** Designed with an extensible backend adapter supporting local open weights execution (vLLM / Ollama / GGUF llama.cpp / Hugging Face Transformers) alongside a verified offline deterministic engine for headless CI environments.
- **Honest Verification & Transparency:** All model interfaces report their exact inference runtime, execution latency, and deterministic verification badges. No simulated functionality is claimed without actual backing implementation.

---

## 4. Product Requirements & Feature Matrix

The platform provides a unified web interface and programmatic engine delivering:

1. **GitHub Repository Integration & Ingestion:** Connects to public repositories to ingest issues, pull requests, commit discussions, and code reviews via public GitHub REST/GraphQL APIs with no credential requirements for public data.
2. **Automated Noise Removal & Thread Summarization:** Transforms chaotic, multi-author developer dialogues into clean, chronological debate structures.
3. **Deep Argumentation Mining:** Detects every proposed technical route, explicitly documenting which proposal won and why alternative options were discarded.
4. **Structured Decision Record Generation (MADR):** Formats output into Markdown Architectural Decision Records and strict schema-validated JSON with confidence metrics (0.0 to 1.0).
5. **Direct Source Code Grounding:** Discovers and annotates source files linked to each architectural conclusion.
6. **Immutable Evidence & Traceability:** Retains exact comment IDs, author attributions, and direct GitHub URL anchors so every single claim can be verified by human maintainers.
7. **Semantic Decision Search & Repository Index:** Allows engineers to search past decisions using keywords, affected file paths, status, or architectural tags.
8. **PR Historical Impact Radar:** Evaluates incoming pull request diffs against indexed decisions to alert engineers: *"You are modifying `src/cache/store.ts`. In PR #142, an in-memory Redis cache was explicitly rejected in favor of an LRU ring buffer due to garbage collection spikes."*

---

## 5. Decision Record Schema (MADR / JSON)

Every recovered engineering decision guarantees the following schema attributes:

```json
{
  "id": "ADR-0042",
  "title": "Use Append-Only Log with Compaction for Metadata Storage",
  "status": "Accepted",
  "context": "High concurrency write contention on SQLite file locks under burst loads.",
  "accepted_approach": "Adopt an append-only WAL log paired with background epoch-based compaction.",
  "rejected_alternatives": [
    {
      "name": "SQLite with WAL mode and busy timeout retry loop",
      "reason_for_rejection": "Under benchmark load, write latency spiked above 450ms due to single-writer lock serializations."
    },
    {
      "name": "Embedded RocksDB C++ binding",
      "reason_for_rejection": "Increased build complexity and broke cross-compilation on musl Linux targets."
    }
  ],
  "technical_tradeoffs": [
    "Slightly increased disk space usage between compaction windows in exchange for 6x write throughput."
  ],
  "related_source_files": [
    "src/storage/wal.ts",
    "src/storage/compactor.ts"
  ],
  "original_discussions": [
    {
      "url": "https://github.com/example/repo/issues/105#issuecomment-892110",
      "comment_id": "892110",
      "author": "lead-maintainer",
      "snippet": "We verified RocksDB fails static linking on Alpine containers..."
    }
  ],
  "confidence_score": 0.94
}
```

---

## 6. Repository Setup & Hacktoberfest Governance

- **Repository Initial Commit:** Contains ONLY `HACKATHON.md`.
- **License:** MIT License (Open-source, permissive).
- **PR-Driven Workflow:** All feature development, tests, examples, frontend, and backend components are introduced strictly via dedicated pull request branches merged into `main`.
- **CI / Quality Gate:** Automated GitHub Actions workflows enforce type safety, linting, unit tests, and model pipeline verification on every pull request.
- **No Credentials:** Zero API keys or secrets are committed or required for public repository analysis.

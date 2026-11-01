# Primordial: Solution and Feature Specification (Corrected)

**Document Identifier:** `PRIMORDIAL-DOC-03-REV2`  
**Project:** Primordial — Open Source Decision Intelligence and Knowledge Recovery  
**Repository:** `primordial-hacktoberfest`  
**Team Members:** Shaurya Negi, Prince Chhikara, Manisha Jain  
**Hackathon:** Hacktoberfest 2026 – Hack Day Sonipat  
**Institution:** Newton School of Technology, Rishihood University  
**Problem Statement:** Problem Statement 06 — Open Source Decision Intelligence and Knowledge Recovery  
**Documentation Version:** 2.0.0 (Implementation-Ready Revision)

---

## Table of Contents

1. [Proposed Solution & Phased Vision](#1-proposed-solution--phased-vision)
2. [Project Directory Structure](#2-project-directory-structure)
3. [Core Feature Breakdown & Deep Specification](#3-core-feature-breakdown--deep-specification)
   - [Feature A: GitHub Entity Integration & Ingestion](#feature-a-github-entity-integration--ingestion)
   - [Feature B: Multi-Modal Comment Disambiguation](#feature-b-multi-modal-comment-disambiguation)
   - [Feature C: Context-Preserving Discourse Preprocessing](#feature-c-context-preserving-discourse-preprocessing)
   - [Feature D: Discourse Decision Detection Engine](#feature-d-discourse-decision-detection-engine)
   - [Feature E: Structured Decision & Rationale Extraction](#feature-e-structured-decision--rationale-extraction)
   - [Feature F: Two-Level Evidence Verification](#feature-f-two-level-evidence-verification)
   - [Feature G: MADR 3.0.0 Markdown Document Generation](#feature-g-madr-300-markdown-document-generation)
   - [Feature H: Primordial CLI Interface (Phase 1 Core)](#feature-h-primordial-cli-interface-phase-1-core)
   - [Feature I: Backend API & Storage (Phase 2)](#feature-i-backend-api--storage-phase-2)
   - [Feature J: React Web Dashboard (Phase 3)](#feature-j-react-web-dashboard-phase-3)
4. [MoSCoW Feature Prioritization Matrix](#4-moscow-feature-prioritization-matrix)
5. [Canonical Data Schema Specification](#5-canonical-data-schema-specification)
   - [Decision Status Semantics](#decision-status-semantics)
   - [Pydantic Domain Schema](#pydantic-domain-schema)
   - [Canonical JSON Example](#canonical-json-example)
6. [Functional Requirements (FR-01 to FR-17)](#6-functional-requirements)
7. [Non-Functional Requirements (NFR-01 to NFR-10)](#7-non-functional-requirements)
8. [User Stories with Gherkin Acceptance Criteria](#8-user-stories-with-gherkin-acceptance-criteria)
9. [System Boundaries, Constraints, and Limitations](#9-system-boundaries-constraints-and-limitations)

---

## 1. Proposed Solution & Phased Vision

Primordial converts unstructured GitHub Issue and Pull Request discussions into structured, evidence-linked Architecture Decision Records (ADRs).

To ensure practical execution within the hackathon timeline, the project follows a disciplined three-phase delivery model:

1. **Phase 1: Core Backend & CLI (MVP Core Target):** Implements the ingestion, preprocessing, AI decision detection, structured extraction, Level 1 technical evidence verification, and MADR compilation, exposed via a command-line interface.
2. **Phase 2: Backend API Service:** Exposes the pipeline via FastAPI (`POST /api/v1/extract`) with SQLite persistence and full-text keyword retrieval.
3. **Phase 3: React Web Dashboard (Later Phase):** Delivers a browser-based Single Page Application with synchronous status loading, a dual-pane ADR preview, and an interactive evidence drawer.

```
+--------------------------------------------------------------------------------------------------------+
|                                    PRIMORDIAL ARCHITECTURAL PIPELINE                                   |
+--------------------------------------------------------------------------------------------------------+
   [ Public GitHub Issue / PR URL ]
                |
                v
   +---------------------------------------------------------------------------------+
   | GitHub REST API Ingestion (Issues, Comments, Reviews, Diff Comments)           |
   +---------------------------------------------------------------------------------+
                |
                v
   +---------------------------------------------------------------------------------+
   | Preprocessing & Chronological Context Budgeting                                 |
   | - Filter automated bots; preserve code fences and diff references               |
   | - Chronological chunking with truncation reporting                              |
   +---------------------------------------------------------------------------------+
                |
                v
   +---------------------------------------------------------------------------------+
   | AI Decision Intelligence Engine (Candidate: Qwen 2.5 7B Instruct via Ollama)   |
   | - Stage 1: Binary Decision Classifier (Detects if thread contains a decision)   |
   | - Stage 2: Structured Rationale Extractor (Extracts options & trade-offs)       |
   +---------------------------------------------------------------------------------+
                |
                v
   +---------------------------------------------------------------------------------+
   | Level 1 Technical Evidence Verification                                         |
   | - Validates cited comment IDs and permalinks physically exist in fetched data   |
   | - Level 2 Semantic validation remains explicitly human-reviewed                 |
   +---------------------------------------------------------------------------------+
                |
                v
   +---------------------------------------------------------------------------------+
   | Output Artifact Generation                                                      |
   | - Compiles MADR 3.0.0 Markdown document with verified permalinks                |
   | - Emits Canonical JSON; Persists to SQLite in Phase 2; Displays in UI in Phase 3|
   +---------------------------------------------------------------------------------+
```

---

## 2. Project Directory Structure

Every document across the Primordial project conforms to this standardized repository structure:

```text
primordial/
├── backend/                        # Python backend application
│   ├── app/                        # Application source code
│   │   ├── api/                    # FastAPI routers and endpoints (Phase 2)
│   │   ├── core/                   # Configuration, exceptions, logging
│   │   ├── domain/                 # Pydantic schemas and entities
│   │   ├── github/                 # GitHub API client, parser, normalizer
│   │   ├── preprocessing/          # Noise cleaner and context budgeter
│   │   ├── ai/                     # Ollama client, prompts, classifier, extractor, verifier
│   │   ├── adr/                    # MADR 3.0.0 Jinja2 compiler
│   │   ├── storage/                # SQLite connection, SQLModel models, repository (Phase 2)
│   │   ├── cli.py                  # CLI entrypoint (Phase 1 MVP)
│   │   └── main.py                 # FastAPI entrypoint (Phase 2)
│   ├── requirements.txt            # Pinned dependencies
│   ├── .env.example                # Template environment variables
│   └── pytest.ini                  # Pytest configuration
├── frontend/                       # React frontend SPA (Phase 3)
│   ├── src/                        # React TypeScript sources
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── examples/                       # Representative sample inputs and actual outputs
│   ├── sample_input.json           # Raw ingested GitHub thread fixture
│   ├── generated_decision.json     # Extracted canonical JSON payload
│   └── 0001-sample-output.md       # Compiled MADR 3.0.0 output
├── tests/                          # Automated test suite
│   ├── fixtures/                   # Static JSON mock responses
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
├── docs/                           # Project documentation & ADR repository
│   └── adr/                        # MADR records generated for Primordial itself
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI workflow
├── .gitignore
├── LICENSE                         # Apache-2.0 or MIT
└── README.md                       # Master project overview and setup instructions
```

---

## 3. Core Feature Breakdown & Deep Specification

### Feature A: GitHub Entity Integration & Ingestion
- **Description:** Parses public GitHub URLs, identifies target repositories and entity numbers, and fetches complete discussion threads via the GitHub REST API v3.
- **Specification:**
  - Validates URLs matching: `^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)/(?P<type>issues|pull)/(?P<number>\d+)$`.
  - Operates unauthenticated by default (60 requests/hr rate limit).
  - Inspects the backend environment variable `GITHUB_TOKEN` from `.env`. When present, attaches it as `Authorization: Bearer <token>`, increasing the limit to 5,000 requests/hr.
  - Never transmits or accepts GitHub tokens via frontend request headers.
  - Monitors `x-ratelimit-remaining` and `x-ratelimit-reset`. If the limit is reached, raises a `GitHubRateLimitExceededException` with the exact reset time.

### Feature B: Multi-Modal Comment Disambiguation
- **Description:** Collects discussion data across distinct GitHub REST API endpoints rather than assuming a single monolithic resource.
- **Specification:**
  - Pull Requests query three distinct endpoints:
    1. Issue-level conversation comments (`/repos/{owner}/{repo}/issues/{number}/comments`).
    2. Diff-level inline review comments (`/repos/{owner}/{repo}/pulls/{number}/comments`).
    3. Review summary records (`/repos/{owner}/{repo}/pulls/{number}/reviews`).
  - Standard Issues query issue details and conversation comments.
  - Handles RFC 5988 `Link` pagination up to a configurable ceiling of 250 comments per thread.

### Feature C: Context-Preserving Discourse Preprocessing
- **Description:** Cleans raw conversational transcripts while preserving all technical substance.
- **Specification:**
  - Filters automated bot messages based on author name patterns (`*bot*`, `github-actions`).
  - Drops empty comments and standalone reaction emojis (`+1`, `:heart:`).
  - Preserves markdown code fences (```` ```...``` ````), inline backticks, file diff references, and line numbers.
  - Preserves unique GitHub comment IDs, author logins, timestamps, and permalinks.
  - Implements **chronological chunking**: If total discussion tokens exceed the model's budget (ceiling: 12,000 tokens), the preprocessor chunks the conversation chronologically with 2-comment overlaps, explicitly recording `was_truncated: true` and reporting the processed comment ratio.

### Feature D: Discourse Decision Detection Engine
- **Description:** Evaluates whether a discussion culminated in an architectural or technical decision.
- **Specification:**
  - Stage 1 binary classifier evaluates the thread and returns `is_decision: bool`, `confidence_score: float` (0.0 to 1.0), and `reasoning: str`.
  - Distinguishes technical decisions (library adoption, protocol changes, refactoring strategies) from routine maintenance (typo fixes, bug patches, dependency bumps).
  - If `is_decision` is `false`, the pipeline terminates early with an informational summary, preventing fabricated decision records.

### Feature E: Structured Decision & Rationale Extraction
- **Description:** Extracts multi-dimensional architectural rationale into the canonical Pydantic domain schema.
- **Specification:**
  - Mandatory extraction fields: `title`, `status`, `context_and_problem`, `decision_drivers`, `chosen_option`, `considered_options`, `consequences`, and `evidence_catalog`.
  - If `status` is `proposed`, `rejected`, or `insufficient_evidence`, `chosen_option` must be `null`.
  - Rejection reasons are recorded for rejected options. If the discussion does not disclose why an alternative was dismissed, `rejection_reason` is set to `null` or `"Unspecified in public thread"`. The model is strictly instructed never to invent missing rationale.

### Feature F: Two-Level Evidence Verification
- **Description:** Explicitly separates technical link verification from semantic claim verification.
- **Specification:**
  - **Level 1: Technical Verification (Automated):**
    - Verifies that cited `comment_id` physically exists in the fetched GitHub payload.
    - Verifies that the cited author and timestamp match the comment author and timestamp.
    - Constructs the canonical permalink (`#issuecomment-XXXXX` or `#discussion_rXXXXX`).
    - If a cited ID does not exist in the source payload, the validator flags it as unverified and removes the broken citation.
  - **Level 2: Semantic Verification (Human-Assisted):**
    - Assesses whether the excerpt logically entails the extracted claim.
    - Primordial clearly documents that Level 2 verification requires human maintainer review. The system does not claim 100% semantic correctness.

### Feature G: MADR 3.0.0 Markdown Document Generation
- **Description:** Formats the extracted decision into an industry-standard Markdown document conforming to MADR 3.0.0.
- **Specification:**
  - Standardized filename: `{number}-{slug}.md`.
  - Required sections: `Context and Problem Statement`, `Decision Drivers`, `Considered Options`, `Decision Outcome`, `Pros and Cons of the Options`.
  - Primordial extension section: `Evidence & Verification Log (Level 1 Technical Verification)`.

### Feature H: Primordial CLI Interface (Phase 1 Core)
- **Description:** Standalone command-line executable providing complete extraction without browser overhead.
- **Specification:**
  - Invocation: `primordial extract <url> [--format markdown|json] [--output file] [--fixture path]`.
  - Returns exit code 0 on success, exit code 1 on pipeline error, exit code 2 on invalid input.

### Feature I: Backend API & Storage (Phase 2)
- **Description:** FastAPI service exposing synchronous extraction and local persistence.
- **Specification:**
  - `POST /api/v1/extract`: Synchronous extraction returning the canonical response envelope.
  - SQLite database in WAL mode storing decision records and FTS5 search index.
  - `GET /api/v1/decisions`: Search and list historical decisions.

### Feature J: React Web Dashboard (Phase 3)
- **Description:** Single-page user interface for browser-based interaction.
- **Specification:**
  - Single input search bar with example target buttons.
  - Indeterminate loading spinner for synchronous extraction.
  - Dual-pane results viewer: Left pane renders MADR Markdown; right pane renders interactive evidence cards.

---

## 4. MoSCoW Feature Prioritization Matrix

```
+----------------------------------------------------------------------------------------------------+
|                                    MOSCOW FEATURE MATRIX                                           |
+----------------+-------------------------------------+---------------------------------------------+
| Priority Level | Feature Name                        | Phase & Description                         |
+----------------+-------------------------------------+---------------------------------------------+
| MUST HAVE      | GitHub URL Parser & REST Client     | Phase 1: Ingests public issues/PRs via REST |
| (MVP Core)     | Multi-Modal Comment Disambiguation  | Phase 1: Distinguishes review vs issue cmts |
|                | Conversational Preprocessor         | Phase 1: Strips bots, preserves code blocks |
|                | Chronological Context Budgeter      | Phase 1: Chunks threads exceeding budget    |
|                | Stage 1 Decision Classifier Gate    | Phase 1: Filters out bug reports/chores     |
|                | Stage 2 Structured Extractor        | Phase 1: Extracts canonical JSON schema     |
|                | Level 1 Technical Evidence Verifier | Phase 1: Matches cited IDs to real comments |
|                | MADR 3.0.0 Markdown Compiler        | Phase 1: Generates standard MADR documents  |
|                | Primordial CLI Interface            | Phase 1: Terminal entrypoint (`cli.py`)     |
|                | Local Open-Weight Model Support     | Phase 1: Ollama candidate `qwen2.5:7b`      |
+----------------+-------------------------------------+---------------------------------------------+
| SHOULD HAVE    | FastAPI Backend Wrapper             | Phase 2: Exposes POST /api/v1/extract       |
| (High Value)   | Local SQLite Storage (WAL Mode)     | Phase 2: Persists decisions in local DB     |
|                | SQLite FTS5 Full-Text Search        | Phase 2: Keyword search across past ADRs    |
|                | React Web Dashboard                 | Phase 3: Single-page UI with dual-pane view |
|                | Interactive Evidence Drawer         | Phase 3: Click citation reveals quote card  |
+----------------+-------------------------------------+---------------------------------------------+
| COULD HAVE     | Batch PR Ingestion Script           | Phase 3: Sequential CLI batch execution     |
| (If Time)      | Offline Fixture Demonstration Mode  | Phase 2: Ingest from local mock JSON        |
|                | Markdown Clipboard Copy & Download  | Phase 3: One-click export in web dashboard  |
+----------------+-------------------------------------+---------------------------------------------+
| FUTURE SCOPE   | Asynchronous Job Queue & Polling    | Post-Hackathon: Celery/Redis background jobs|
| (Beyond MVP)   | GitHub Discussions GraphQL Ingestion| Post-Hackathon: GraphQL Discussions mining  |
|                | Automated Repository Crawlers       | Post-Hackathon: Index 1,000+ issues at once |
|                | Semantic Vector Embeddings (RAG)    | Post-Hackathon: Dense retrieval across orgs |
|                | GitHub Action CI/CD Bot             | Post-Hackathon: Auto-draft ADR on PR merge  |
+----------------+-------------------------------------+---------------------------------------------+
```

---

## 5. Canonical Data Schema Specification

Every document, backend module, test case, and API response in Primordial conforms to this single canonical schema.

### Decision Status Semantics

| Status Value | Strict Semantic Meaning | Allowed `chosen_option` Value |
|---|---|---|
| `accepted` | An architectural solution was explicitly accepted or merged by maintainers. | Must be a populated `ChosenOption` object. |
| `rejected` | The evaluated architectural proposal was explicitly rejected or closed. | Must be `null`. |
| `proposed` | An architectural alternative was proposed and discussed, but no final maintainer decision was reached. | Must be `null`. |
| `superseded` | A historical decision that was subsequently overridden by a newer architectural choice. | May be populated or `null` depending on context. |
| `insufficient_evidence` | The discussion touches on architectural choices, but critical context, rationale, or outcomes are missing from the public thread. | Must be `null`. |

---

### Pydantic Domain Schema

```python
# backend/app/domain/schemas.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DecisionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class OptionStatus(str, Enum):
    CHOSEN = "chosen"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"

class ChosenOption(BaseModel):
    name: str = Field(..., description="Name of the accepted technical solution")
    description: str = Field(..., description="Technical explanation of the selected solution")
    evidence_ids: List[str] = Field(default_factory=list, description="List of cited comment IDs")

class ConsideredOption(BaseModel):
    name: str = Field(..., description="Name of the evaluated alternative")
    status: OptionStatus = Field(..., description="Whether this option was chosen, rejected, or unresolved")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection, or null if unstated")
    evidence_ids: List[str] = Field(default_factory=list, description="List of cited comment IDs")

class Consequences(BaseModel):
    positive: List[str] = Field(default_factory=list, description="List of benefits")
    negative: List[str] = Field(default_factory=list, description="List of liabilities or trade-offs")

class DecisionPayload(BaseModel):
    title: str = Field(..., description="Active-voice architectural decision title")
    status: DecisionStatus = Field(..., description="Standardized decision status")
    context_and_problem: str = Field(..., description="Problem description and technical drivers")
    decision_drivers: List[str] = Field(default_factory=list, description="List of decision drivers")
    chosen_option: Optional[ChosenOption] = Field(None, description="Chosen option (null if not accepted)")
    considered_options: List[ConsideredOption] = Field(default_factory=list, description="All evaluated options")
    consequences: Consequences = Field(default_factory=Consequences, description="Positive and negative trade-offs")

class EvidenceItem(BaseModel):
    comment_id: str = Field(..., description="Source comment ID from GitHub")
    author: str = Field(..., description="Author GitHub login handle")
    timestamp: datetime = Field(..., description="ISO-8601 comment creation timestamp")
    html_url: str = Field(..., description="Direct GitHub permalink with comment anchor")
    claim_supported: str = Field(..., description="Summary of the claim supported by this comment")
    verbatim_excerpt: Optional[str] = Field(None, description="Verbatim quote from the comment body")
    is_technically_verified: bool = Field(True, description="True if comment ID physically exists in discussion")

class ClassificationResult(BaseModel):
    is_decision: bool = Field(..., description="True if discussion represents an architectural decision")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model heuristic score (not calibrated probability)")
    reasoning: str = Field(..., description="Brief explanation of classification verdict")

class ContextProcessingMetadata(BaseModel):
    total_comments_ingested: int
    substantive_comments_retained: int
    was_truncated: bool
    processing_note: Optional[str] = None

class VerifiedDecisionResponse(BaseModel):
    extraction_id: str
    repository: str
    source_url: str
    entity_type: str
    entity_number: int
    extracted_at: datetime
    classification: ClassificationResult
    decision: Optional[DecisionPayload] = None
    evidence_catalog: List[EvidenceItem] = Field(default_factory=list)
    context_metadata: ContextProcessingMetadata
    madr_content: Optional[str] = None
```

---

### Canonical JSON Example

```json
{
  "extraction_id": "ext_88d120a1",
  "repository": "nodejs/node",
  "source_url": "https://github.com/nodejs/node/pull/41749",
  "entity_type": "pull_request",
  "entity_number": 41749,
  "extracted_at": "2026-11-01T01:30:00Z",
  "classification": {
    "is_decision": true,
    "confidence_score": 0.94,
    "reasoning": "Discussion reaches consensus to incorporate the undici HTTP engine as the foundation for a built-in fetch API."
  },
  "decision": {
    "title": "Adopt Undici as the Foundation for Built-in Fetch API",
    "status": "accepted",
    "context_and_problem": "Node.js lacked a standard HTTP client compliant with web standards. Developers relied on third-party npm packages, creating ecosystem fragmentation. How should Node.js provide an ergonomic, spec-compliant global fetch() without compromising performance?",
    "decision_drivers": [
      "Strict compliance with WHATWG Fetch Living Standard",
      "High throughput HTTP/1.1 pipelining performance",
      "Maintenance within the official Node.js GitHub organization",
      "Avoidance of third-party external governance dependencies"
    ],
    "chosen_option": {
      "name": "Adopt undici as the core HTTP engine",
      "description": "Integrate undici into Node core to power global fetch().",
      "evidence_ids": ["1034981"]
    },
    "considered_options": [
      {
        "name": "Adopt undici as the core HTTP engine",
        "status": "chosen",
        "rejection_reason": null,
        "evidence_ids": ["1034981"]
      },
      {
        "name": "Bundle community node-fetch",
        "status": "rejected",
        "rejection_reason": "Diverged from latest WHATWG specifications and had independent external maintenance.",
        "evidence_ids": ["1034981"]
      },
      {
        "name": "Write C++ HTTP client from scratch",
        "status": "rejected",
        "rejection_reason": "Excessive implementation effort and maintenance overhead on Node.js core team.",
        "evidence_ids": ["1035120"]
      },
      {
        "name": "Status quo (rely on userland packages)",
        "status": "rejected",
        "rejection_reason": "Ongoing developer friction across browser and server runtimes.",
        "evidence_ids": []
      }
    ],
    "consequences": {
      "positive": [
        "Native, zero-dependency fetch() available globally in Node.js",
        "High throughput via llhttp parser and connection pooling"
      ],
      "negative": [
        "Increased code surface area in Node.js core runtime",
        "Initial rollout requires experimental flag due to global scope addition"
      ]
    }
  },
  "evidence_catalog": [
    {
      "comment_id": "1034981",
      "author": "mcollina",
      "timestamp": "2022-02-03T14:22:10Z",
      "html_url": "https://github.com/nodejs/node/pull/41749#issuecomment-1034981",
      "claim_supported": "Choice of undici and rejection of node-fetch based on spec compliance and throughput.",
      "verbatim_excerpt": "Undici is maintained by the Node.js team and strictly aligns with the web platform standard.",
      "is_technically_verified": true
    },
    {
      "comment_id": "1035120",
      "author": "jasnell",
      "timestamp": "2022-02-03T16:05:44Z",
      "html_url": "https://github.com/nodejs/node/pull/41749#issuecomment-1035120",
      "claim_supported": "Rejection of from-scratch C++ client.",
      "verbatim_excerpt": "Building another HTTP client in C++ from scratch would duplicate years of work already put into undici.",
      "is_technically_verified": true
    }
  ],
  "context_metadata": {
    "total_comments_ingested": 112,
    "substantive_comments_retained": 22,
    "was_truncated": false,
    "processing_note": "Complete substantive thread processed within token budget."
  },
  "madr_content": "# 0001 - Adopt Undici as the Foundation for Built-in Fetch API\n\n* **Status:** accepted\n* **Date:** 2022-02-03..."
}
```

---

## 6. Functional Requirements

### Group 1: Ingestion & URL Parsing
- **FR-01:** The system MUST accept a public GitHub URL in the format `https://github.com/:owner/:repo/(issues|pull)/:number`.
- **FR-02:** The system MUST validate the URL syntax and return an immediate descriptive error message if invalid.
- **FR-03:** The system MUST fetch the primary entity description (Issue or PR body) and core metadata (author, created_at, state).
- **FR-04:** The system MUST fetch conversation comments for issues and PRs, traversing pagination up to a maximum limit of 250 comments per thread.
- **FR-05:** For Pull Requests, the system MUST fetch inline code review comments and review summary records in addition to conversation comments.
- **FR-06:** The system MUST read `GITHUB_TOKEN` from backend environment configuration to increase rate limits to 5,000 req/hr.

### Group 2: Preprocessing & Context Construction
- **FR-07:** The system MUST filter out automated bot messages matching known bot author patterns (`*bot*`, `github-actions`).
- **FR-08:** The system MUST preserve markdown code fences, backticks, and technical identifiers during text normalization.
- **FR-09:** The system MUST maintain a lookup mapping containing each comment's unique GitHub ID, author, timestamp, and HTML URL.
- **FR-10:** If discussion tokens exceed the model budget (12,000 tokens), the system MUST apply chronological chunking and record `was_truncated: true` in the output.

### Group 3: AI Decision Intelligence & Extraction
- **FR-11:** The system MUST classify whether the discussion represents a technical decision (`is_decision: bool`).
- **FR-12:** If `is_decision == false`, the system MUST return a concise explanatory summary and terminate further extraction without generating an ADR.
- **FR-13:** If `is_decision == true`, the system MUST extract the Problem Context, Decision Drivers, Chosen Option, Considered Options, and Consequences into the canonical schema.
- **FR-14:** If a specific decision element (e.g., rejection reason) is not stated in the source text, the system MUST output `null` or `"Unspecified in public thread"` rather than guessing.

### Group 4: Evidence Verification, Formatting & Storage
- **FR-15:** The system MUST perform Level 1 technical verification, validating that every cited comment ID physically exists in the fetched discussion.
- **FR-16:** The system MUST generate a valid MADR 3.0.0 Markdown document containing direct permalinks to source comments.
- **FR-17:** In Phase 1, the system MUST support execution via CLI (`primordial extract <url>`). In Phase 2, the system MUST support synchronous execution via FastAPI (`POST /api/v1/extract`) and SQLite persistence.

---

## 7. Non-Functional Requirements

- **NFR-01 (Privacy & Sovereignty):** All AI inference MUST execute locally using an open-weight model (candidate: Qwen 2.5 7B Instruct via Ollama). No discussion content may be sent to paid, closed-source cloud APIs.
- **NFR-02 (Performance & Latency):** Ingestion, preprocessing, and local LLM extraction for a standard discussion thread (10–50 comments) SHOULD complete within 45 seconds on standard developer laptops (e.g., Apple Silicon M-series or 8-core x86 with 16GB RAM). Exact hardware-dependent benchmarks are marked PENDING until measured.
- **NFR-03 (Determinism & Schema Validity):** The AI extraction service MUST utilize Ollama JSON format mode to guarantee that outputs parse into the Pydantic schema without JSON syntax errors.
- **NFR-04 (API Safety & Compliance):** The system MUST operate entirely via read-only GitHub API calls. The system MUST NEVER attempt to create, edit, or post comments, issues, or pull requests to external repositories.
- **NFR-05 (Resilience):** If an individual comment contains non-UTF-8 characters, the preprocessor MUST sanitize the stream without crashing.
- **NFR-06 (Portability):** The backend MUST run on Python 3.11+ across macOS, Linux, and Windows (WSL2).
- **NFR-07 (Code Coverage):** Core ingestion, parsing, pre-processing, and verification modules MUST achieve a minimum of 80% unit test coverage using Pytest.

---

## 8. User Stories with Gherkin Acceptance Criteria

### User Story 1: CLI Decision Extraction (Phase 1 MVP)
**As an** open-source contributor,  
**I want to** run a CLI command with a public GitHub PR URL,  
**So that** I can recover the architectural rationale without reading 100+ comments manually.

```gherkin
Scenario: Successful decision extraction from a public Pull Request via CLI
  Given the Primordial backend environment is configured with Ollama running
  And a valid public GitHub PR URL "https://github.com/nodejs/node/pull/41749"
  When the user executes "primordial extract https://github.com/nodejs/node/pull/41749"
  Then the system should parse owner as "nodejs", repo as "node", and number as 41749
  And the system should fetch the PR description and comments via GitHub REST API
  And the system should preprocess the text, stripping bot comments while preserving code blocks
  And the local LLM should classify the discussion as an architectural decision
  And the system should return a validated canonical JSON payload containing the chosen option "undici"
  And the system should generate a MADR 3.0.0 document with valid links to GitHub comments
```

### User Story 2: Handling a Routine Bug Report
**As a** repository maintainer,  
**I want** Primordial to recognize when an issue contains no architectural decisions,  
**So that** the system does not fabricate false ADRs for routine bug fixes.

```gherkin
Scenario: Analyzing an issue that is purely a routine bug fix
  Given a public GitHub Issue URL for a routine bug fix
  When the user runs "primordial extract <bug_fix_url>"
  Then the system should fetch and preprocess the thread
  And the Decision Classifier should return "is_decision: false"
  And the system should NOT generate an Architectural Decision Record
  And the CLI should output: "Informational: No Architectural Decision Detected in this thread."
```

### User Story 3: Level 1 Technical Evidence Verification
**As a** software engineer,  
**I want** every cited comment ID in the ADR to be validated against the source thread,  
**So that** I do not encounter broken permalinks or hallucinated comment IDs.

```gherkin
Scenario: Verifying comment ID citations against source transcripts
  Given an ingested PR containing comments with IDs ["1034981", "1035120"]
  When the LLM outputs an extracted decision citing comment ID "1034981" for the chosen option
  Then the Evidence Verifier should confirm "1034981" exists in the ingested payload
  And the generated MADR document should contain a permalink ending with "#issuecomment-1034981"
  And the item should be marked "is_technically_verified: true"
```

---

## 9. System Boundaries, Constraints, and Limitations

1. **Context Window Ceiling:** While modern models support large context windows, local consumer hardware incurs latency and memory pressure above 12,000 tokens. Primordial implements chronological chunking for long threads.
2. **Read-Only Operation:** Primordial strictly reads public data. It never writes back to GitHub repositories.
3. **Public Discussions Only:** Primordial operates exclusively on public discussions. Decisions made in private Slack channels, Discord chats, or offline calls cannot be recovered unless maintainers recorded them in a public comment.
4. **Single-Thread Focus for MVP:** The Phase 1 MVP and Phase 2 API process one Issue or PR URL per invocation. Cross-issue synthesis spanning multiple disjointed threads is reserved for post-hackathon development.

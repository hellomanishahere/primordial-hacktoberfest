# Primordial: Complete Technical Research, Implementation, and Testing Master Reference (Corrected)

**Document Identifier:** `PRIMORDIAL-DOC-06-REV2`  
**Project:** Primordial — Open Source Decision Intelligence and Knowledge Recovery  
**Repository:** `primordial-hacktoberfest`  
**Team Members:** Shaurya Negi, Prince Chhikara, Manisha Jain  
**Hackathon:** Hacktoberfest 2026 – Hack Day Sonipat  
**Institution:** Newton School of Technology, Rishihood University  
**Problem Statement:** Problem Statement 06 — Open Source Decision Intelligence and Knowledge Recovery  
**Documentation Version:** 2.0.0 (Implementation-Ready Revision)

---

## Table of Contents

1. [Deep Technical Research: GitHub API Ecosystem](#1-deep-technical-research-github-api-ecosystem)
2. [AI, NLP & Argumentation Mining Research](#2-ai-nlp--argumentation-mining-research)
3. [ADR & MADR Specification Standards](#3-adr--madr-specification-standards)
4. [Standardized Repository Structure](#4-standardized-repository-structure)
5. [End-to-End API Contract Specification](#5-end-to-end-api-contract-specification)
6. [Canonical Pydantic Data Models](#6-canonical-pydantic-data-models)
7. [Production AI Prompt Templates](#7-production-ai-prompt-templates)
8. [Comprehensive Testing Strategy & Quality Assurance](#8-comprehensive-testing-strategy--quality-assurance)
   - [Planned vs. Implemented vs. Executed Test Status](#planned-vs-implemented-vs-executed-test-status)
   - [Unit Testing Specifications & Fixtures](#unit-testing-specifications--fixtures)
   - [Integration Testing Specifications](#integration-testing-specifications)
   - [Failure & Resilience Testing Specifications](#failure--resilience-testing-specifications)
9. [Quantitative & Qualitative Evaluation Metrics](#9-quantitative--qualitative-evaluation-metrics)
10. [Security, Privacy, and Token Reliability Controls](#10-security-privacy-and-token-reliability-controls)
11. [12-Stage Phased Implementation Roadmap](#11-12-stage-phased-implementation-roadmap)
12. [Team Work Division & Integration Contracts](#12-team-work-division--integration-contracts)
13. [Live Hackathon Demonstration Plan & Script](#13-live-hackathon-demonstration-plan--script)
14. [Engineering Risks, Trade-Offs, and Mitigations](#14-engineering-risks-trade-offs-and-mitigations)
15. [Future Roadmap & Beyond-MVP Horizons](#15-future-roadmap--beyond-mvp-horizons)

---

## 1. Deep Technical Research: GitHub API Ecosystem

To implement an extraction pipeline, developers must understand how GitHub structures its collaborative discourse across multiple independent REST resources.

```
+-------------------------------------------------------------------------------------------------------------------+
|                                       GITHUB REST API RESOURCE MAP                                                |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Resource Type        | Endpoint Pattern                              | Primary Data Extracted                     |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Issue Details        | `GET /repos/{owner}/{repo}/issues/{id}`       | Issue title, initial problem description,  |
|                      |                                               | author, open/closed state, labels          |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Issue Conversation   | `GET /repos/{owner}/{repo}/issues/{id}/`      | High-level conversational debates, RFC     |
| Comments             | `comments?per_page=100`                       | discussions, consensus declarations        |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Pull Request Details | `GET /repos/{owner}/{repo}/pulls/{id}`        | PR title, implementation rationale, diff   |
|                      |                                               | stats, merge status, base/head branches    |
+----------------------+-----------------------------------------------+--------------------------------------------+
| PR Inline Review     | `GET /repos/{owner}/{repo}/pulls/{id}/`       | Code-level review comments attached to diff|
| Comments             | `comments?per_page=100`                       | hunks; low-level trade-offs & edge cases   |
+----------------------+-----------------------------------------------+--------------------------------------------+
| PR Review Summaries  | `GET /repos/{owner}/{repo}/pulls/{id}/`       | Formal maintainer verdicts (APPROVED,      |
|                      | `reviews?per_page=100`                        | CHANGES_REQUESTED) and review bodies       |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Rate Limit Status    | `GET /rate_limit`                             | Core remaining requests, reset timestamps  |
+----------------------+-----------------------------------------------+--------------------------------------------+
```

### Essential API Nuances & Traps
1. **Pull Requests are Issues with Additional Review Endpoints:** In GitHub's data model, every Pull Request is also an Issue. Calling `/repos/{owner}/{repo}/issues/{id}/comments` on a Pull Request returns top-level conversational comments. However, that endpoint **omits inline code review comments**. To collect the entire conversation, the client must query both `/issues/{id}/comments` and `/pulls/{id}/comments`.
2. **Pagination via RFC 5988 `Link` Headers:** The GitHub REST API does not provide total page counts in response bodies. Pagination must be parsed from the HTTP `Link` response header:
   ```http
   Link: <https://api.github.com/repositories/123/issues/456/comments?page=2&per_page=100>; rel="next",
         <https://api.github.com/repositories/123/issues/456/comments?page=5&per_page=100>; rel="last"
   ```
3. **Rate Limits & Header Inspection:**
   - Unauthenticated: 60 requests/hour per IP.
   - Authenticated: 5,000 requests/hour per token.
   - Every response contains `x-ratelimit-remaining` and `x-ratelimit-reset` (Unix epoch seconds). The client inspects these headers on every call.
4. **Why REST for MVP instead of GraphQL:**
   - The GitHub GraphQL API requires nested queries and cursor pagination.
   - GitHub Discussions is only supported via GraphQL, but for standard Issues and Pull Requests, the REST API is simpler, stateless, and significantly faster to mock in Pytest fixtures. REST is the designated protocol for the hackathon MVP. GraphQL is reserved for post-hackathon Discussions integration.

---

## 2. AI, NLP & Argumentation Mining Research

### Argumentation Mining Foundations
Extracting decisions from unstructured chat is a specialized subfield of Natural Language Processing known as **Argumentation Mining** ([Lippi & Torroni, 2016](https://dl.acm.org/doi/10.1145/2850417)).

In software discussions, argumentation unfolds dialectically:
1. **Major Premise (Context / Driver):** A performance bottleneck, security constraint, or missing standard API is identified.
2. **Proposal (Claim A):** An author submits a pull request proposing Solution A.
3. **Attack / Rebuttal (Premise B):** A reviewer counters that Solution A increases memory usage or breaks backwards compatibility.
4. **Counter-Proposal (Claim B):** A maintainer suggests Solution B as a compromise.
5. **Synthesis & Resolution (Consensus):** The participants converge on an accepted outcome with explicit trade-offs.

### Why Local Open-Weight Models (Candidate: Qwen 2.5 7B) are Appropriate
- **No Proprietary Vendor Lock-in:** Open-source projects cannot rely on paid, proprietary cloud APIs (e.g., OpenAI, Anthropic) that may change pricing or discontinue model endpoints.
- **Data Privacy & Enterprise Sovereignty:** Many engineering teams operate internal GitHub enterprise instances or discuss unreleased security patches that cannot be sent to commercial cloud providers.
- **Structured JSON Mode:** Modern instruction-tuned models like `qwen2.5:7b-instruct` natively support grammar-constrained decoding (Ollama JSON format mode), preventing JSON parse failures.

---

## 3. ADR & MADR Specification Standards

### Architectural Decision Records (ADR)
An Architectural Decision Record (ADR) is a lightweight document capturing an important architectural decision made along with its context and consequences ([Nygard, 2011](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).

### Markdown Architectural Decision Records (MADR 3.0.0)
Primordial standardizes on **MADR 3.0.0** ([https://adr.github.io/madr/](https://adr.github.io/madr/)), which provides a structured Markdown template designed for git version control.

### Sample Generated MADR 3.0.0 Document

> **Note on Example Fixture:** The topic below (Node.js PR #41749 and undici) is a verified historical decision. Comment IDs (`1034981`, `1035120`, `1036044`) are illustrative test fixtures used to demonstrate schema formatting.

```markdown
# 0001 - Adopt Undici as the Foundation for Built-in Fetch API

* **Status:** accepted
* **Date:** 2022-02-03
* **Deciders:** Node.js Technical Steering Committee (TSC) & Contributors
* **Source Discussion:** [nodejs/node PR #41749](https://github.com/nodejs/node/pull/41749)

## Context and Problem Statement

For years, Node.js lacked a built-in HTTP client compliant with web standards. Developers relied on third-party npm packages (`axios`, `node-fetch`), causing ecosystem fragmentation. How should Node.js provide an ergonomic, spec-compliant global `fetch()` without compromising performance?

## Decision Drivers

* Conformance with the WHATWG Fetch Living Standard
* High throughput and low latency HTTP/1.1 performance
* Long-term maintainability within the official Node.js GitHub organization
* Zero external third-party dependencies outside the Node.js governance umbrella

## Considered Options

* **Adopt undici as the core HTTP engine (Chosen)**
* **Bundle community node-fetch**
* **Write C++ HTTP client from scratch**
* **Status quo (rely on userland npm packages)**

## Decision Outcome

Chosen option: **Adopt undici as the core HTTP engine**, because `undici` is an official Node.js project written from scratch to maximize throughput using the `llhttp` parser, conforms strictly to WHATWG standards, and avoids external vendor dependencies.

### Positive Consequences

* Developers gain native, zero-dependency `fetch()` matching browser environments.
* High request throughput via `undici` connection pooling.
* Single source of truth for web platform standard APIs in Node core.

### Negative Consequences

* Introduces significant code surface area into Node.js core runtime.
* Global scope addition requires an experimental feature flag during initial rollout (`--experimental-fetch`).

## Pros and Cons of the Options

### Adopt undici as the core HTTP engine (Chosen)

* Good, because it provides significantly higher throughput compared to legacy `http.request`.
* Good, because it is maintained within the official Node.js GitHub organization.
* Bad, because it initially added significant code to the core repository.
* *Evidence Citation:* [Comment #1034981](https://github.com/nodejs/node/pull/41749#issuecomment-1034981)

### Bundle community node-fetch

* Good, because millions of developers were already familiar with the API.
* Bad, because it diverged from latest WHATWG specifications.
* Bad, because governance is external to the Node.js project.
* *Evidence Citation:* [Comment #1034981](https://github.com/nodejs/node/pull/41749#issuecomment-1034981)

### Write C++ HTTP client from scratch

* Good, because it would provide direct V8 internal bindings.
* Bad, because the implementation effort and maintenance overhead were prohibitive.
* *Evidence Citation:* [Comment #1035120](https://github.com/nodejs/node/pull/41749#issuecomment-1035120)

## Evidence & Verification Log (Level 1 Technical Verification)

| Target Claim / Option | Author | Comment ID | GitHub Source Permalink | Technical Verification |
|---|---|---|---|---|
| Adopt undici / Reject node-fetch | `@mcollina` | `1034981` | [nodejs/node#41749#issuecomment-1034981](https://github.com/nodejs/node/pull/41749#issuecomment-1034981) | VERIFIED (Comment exists) |
| Reject C++ scratch client | `@jasnell` | `1035120` | [nodejs/node#41749#issuecomment-1035120](https://github.com/nodejs/node/pull/41749#issuecomment-1035120) | VERIFIED (Comment exists) |
| Merge consensus | `@ronag` | `1036044` | [nodejs/node#41749#issuecomment-1036044](https://github.com/nodejs/node/pull/41749#issuecomment-1036044) | VERIFIED (Comment exists) |
```

---

## 4. Standardized Repository Structure

```text
primordial/
├── backend/                        # Python backend application
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py           # Top-level API router (/api/v1)
│   │   │   └── endpoints/
│   │   │       ├── extract.py      # POST /api/v1/extract (synchronous)
│   │   │       ├── decisions.py    # GET /api/v1/decisions (listing & FTS5 search)
│   │   │       └── health.py       # GET /api/v1/health
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic BaseSettings, .env loader
│   │   │   ├── exceptions.py       # Custom exception hierarchy
│   │   │   └── logging.py          # Structured logging configuration
│   │   ├── domain/
│   │   │   ├── schemas.py          # Canonical Pydantic domain models
│   │   │   └── entities.py         # Internal dataclasses & Enums
│   │   ├── github/
│   │   │   ├── parser.py           # URL validation & regex parser
│   │   │   ├── router.py           # Entity router (issues vs pull)
│   │   │   ├── client.py           # Async httpx client with rate limit handler
│   │   │   └── normalizer.py       # Canonical comment stream builder
│   │   ├── preprocessing/
│   │   │   ├── cleaner.py          # Bot filter, signature & noise stripper
│   │   │   └── budgeter.py         # Chronological chunking & token budgeter
│   │   ├── ai/
│   │   │   ├── ollama_client.py    # Ollama REST connector (JSON mode)
│   │   │   ├── prompts.py          # Stage 1 and Stage 2 prompt templates
│   │   │   ├── classifier.py       # Stage 1 binary decision gate
│   │   │   ├── extractor.py        # Stage 2 structured rationale extractor
│   │   │   └── verifier.py         # Level 1 technical evidence verifier
│   │   ├── adr/
│   │   │   ├── compiler.py         # MADR 3.0.0 Jinja2 generator
│   │   │   └── templates/
│   │   │       └── madr_template.md# Standard MADR 3.0.0 layout
│   │   ├── storage/                # Phase 2 Storage
│   │   │   ├── database.py         # SQLite connection & WAL mode config
│   │   │   ├── models.py           # SQLModel database tables
│   │   │   └── repository.py       # CRUD & SQLite FTS5 search queries
│   │   ├── services/
│   │   │   └── orchestrator.py     # Master 12-stage pipeline orchestrator
│   │   ├── cli.py                  # CLI entrypoint (Phase 1 MVP)
│   │   └── main.py                 # FastAPI application (Phase 2)
│   ├── requirements.txt            # Pinned dependencies
│   ├── .env.example                # Template environment variables
│   └── pytest.ini                  # Pytest configuration
├── frontend/                       # React frontend SPA (Phase 3)
│   ├── src/
│   │   ├── components/
│   │   │   ├── UrlInputBar.tsx
│   │   │   ├── AdrViewer.tsx
│   │   │   ├── EvidenceDrawer.tsx
│   │   │   └── LoadingState.tsx
│   │   ├── services/
│   │   │   └── api.ts              # Axios / Fetch client
│   │   ├── types/
│   │   │   └── decision.ts         # TypeScript interfaces matching backend
│   │   ├── App.tsx
│   │   └── main.tsx
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
├── docs/                           # Documentation & MADR records
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI workflow
├── .gitignore
├── LICENSE                         # Apache-2.0 or MIT
└── README.md                       # Master project overview and setup instructions
```

---

## 5. End-to-End API Contract Specification

### Endpoint: `POST /api/v1/extract`
- **Method:** `POST`
- **URL:** `/api/v1/extract`
- **Purpose:** Ingests a public GitHub Issue or PR URL, executes the complete extraction pipeline synchronously, persists to SQLite, and returns the response envelope.
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "url": "https://github.com/nodejs/node/pull/41749",
    "force_refresh": false
  }
  ```
- **Response Status: 200 OK**
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
      "reasoning": "Technical consensus reached to adopt undici as core HTTP engine."
    },
    "decision": {
      "title": "Adopt Undici as the Foundation for Built-in Fetch API",
      "status": "accepted",
      "context_and_problem": "Node.js lacked a standard HTTP client...",
      "decision_drivers": ["WHATWG spec compliance", "Throughput"],
      "chosen_option": {
        "name": "Adopt undici as core HTTP engine",
        "description": "Integrate undici into Node core.",
        "evidence_ids": ["1034981"]
      },
      "considered_options": [
        {
          "name": "Bundle community node-fetch",
          "status": "rejected",
          "rejection_reason": "Diverged from WHATWG specifications.",
          "evidence_ids": ["1034981"]
        }
      ],
      "consequences": {
        "positive": ["Universal fetch available globally."],
        "negative": ["Added code surface area in core."]
      }
    },
    "evidence_catalog": [
      {
        "comment_id": "1034981",
        "author": "mcollina",
        "timestamp": "2022-02-03T14:22:10Z",
        "html_url": "https://github.com/nodejs/node/pull/41749#issuecomment-1034981",
        "claim_supported": "Choice of undici and rejection of node-fetch.",
        "verbatim_excerpt": "Undici is maintained by the Node.js team and aligns with the standard.",
        "is_technically_verified": true
      }
    ],
    "context_metadata": {
      "total_comments_ingested": 112,
      "substantive_comments_retained": 22,
      "was_truncated": false,
      "processing_note": "Complete thread processed."
    },
    "madr_content": "# 0001 - Adopt Undici...\n\n* **Status:** accepted..."
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Invalid GitHub URL syntax.
  - `404 Not Found`: Repository or discussion not found.
  - `422 Unprocessable Entity`: Discussion is empty or contains only bots.
  - `429 Too Many Requests`: GitHub rate limit reached.
  - `503 Service Unavailable`: Local Ollama service is unreachable.

---

## 6. Canonical Pydantic Data Models

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

class ExtractRequest(BaseModel):
    url: str = Field(..., description="Public GitHub Issue or PR URL")
    force_refresh: bool = False

class ChosenOption(BaseModel):
    name: str = Field(..., description="Name of accepted solution")
    description: str = Field(..., description="Technical explanation")
    evidence_ids: List[str] = Field(default_factory=list)

class ConsideredOption(BaseModel):
    name: str = Field(..., description="Name of evaluated option")
    status: OptionStatus = Field(..., description="Option status")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason or null")
    evidence_ids: List[str] = Field(default_factory=list)

class Consequences(BaseModel):
    positive: List[str] = Field(default_factory=list)
    negative: List[str] = Field(default_factory=list)

class DecisionPayload(BaseModel):
    title: str = Field(..., description="Active-voice decision title")
    status: DecisionStatus = Field(..., description="Standardized decision status")
    context_and_problem: str = Field(..., description="Problem description")
    decision_drivers: List[str] = Field(default_factory=list)
    chosen_option: Optional[ChosenOption] = None
    considered_options: List[ConsideredOption] = Field(default_factory=list)
    consequences: Consequences = Field(default_factory=Consequences)

class EvidenceItem(BaseModel):
    comment_id: str
    author: str
    timestamp: datetime
    html_url: str
    claim_supported: str
    verbatim_excerpt: Optional[str] = None
    is_technically_verified: bool = True

class ClassificationResult(BaseModel):
    is_decision: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

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

## 7. Production AI Prompt Templates

### Prompt 1: Binary Decision Classifier (Stage 1)

```text
You are a Principal Software Architect analyzing public open-source repository discussions.
Your task is to determine whether the provided GitHub discussion thread culminated in an ARCHITECTURAL OR TECHNICAL DECISION, or whether it is merely routine project maintenance.

AN ARCHITECTURAL DECISION INCLUDES:
- Selecting or replacing a library, protocol, database, or algorithmic strategy.
- Adopting a new API pattern, interface signature, or serialization standard.
- Resolving a debate between competing implementation options with explicit trade-offs.

A NON-DECISION INCLUDES:
- Routine bug fixes (e.g., null checks, typo corrections, off-by-one errors).
- Dependency version bumps without architectural changes.
- Unresolved questions, user support requests, or feature proposals abandoned without discussion.

INSTRUCTIONS:
1. Base your answer strictly on the text provided inside <transcript>.
2. Respond ONLY in valid JSON matching this exact schema:
{
  "is_decision": true | false,
  "confidence_score": 0.0 to 1.0,
  "reasoning": "2-3 sentences explaining why this thread is or is not an architectural decision."
}

<transcript>
{transcript_text}
</transcript>
```

---

### Prompt 2: Structured Decision & Rationale Extractor (Stage 2)

```text
You are an expert Software Architecture Analyst extracting an Architecture Decision Record (ADR) from a GitHub discussion.
Your mission is to decompose this discussion into an objective, factual, evidence-grounded decision model.

CRITICAL ANTI-HALLUCINATION RULES:
1. DO NOT INVENT ALTERNATIVES. Only list an option in "considered_options" if a participant explicitly discussed it in the transcript.
2. DO NOT FABRICATE REJECTION REASONS. If the discussion does not explain why an option was rejected, write null for "rejection_reason".
3. EVIDENCE CITATIONS ARE MANDATORY. For every option, you must attach the exact "evidence_ids" (the COMMENT ID strings) where that option was evaluated.
4. If no accepted decision was reached, set "status" to "proposed" or "insufficient_evidence", and set "chosen_option" to null.

JSON OUTPUT SCHEMA:
{
  "title": "Active voice title (e.g., 'Adopt Undici as Foundation for Built-in Fetch API')",
  "status": "accepted" | "rejected" | "proposed" | "superseded" | "insufficient_evidence",
  "context_and_problem": "Detailed explanation of why this decision was needed and what constraints existed.",
  "decision_drivers": ["List of 2-5 explicit requirements or motivators"],
  "chosen_option": {
    "name": "Name of accepted solution",
    "description": "How the solution works",
    "evidence_ids": ["Comment ID string"]
  } | null,
  "considered_options": [
    {
      "name": "Name of evaluated option",
      "status": "chosen" | "rejected" | "unresolved",
      "rejection_reason": "Why it was rejected, or null if unstated",
      "evidence_ids": ["Comment ID string"]
    }
  ],
  "consequences": {
    "positive": ["1-3 explicit benefits mentioned in discussion"],
    "negative": ["1-3 trade-offs, risks, or liabilities accepted"]
  }
}

<transcript>
{transcript_text}
</transcript>
```

---

## 8. Comprehensive Testing Strategy & Quality Assurance

### Planned vs. Implemented vs. Executed Test Status

To maintain documentation integrity, test cases are clearly categorized:
- **Planned Tests:** Formally specified below with target inputs, expected outputs, and assertions.
- **Implemented Tests:** Tests coded into the repository under `tests/`. (Status: *Pending implementation by coding phase*).
- **Executed Tests:** Tests successfully run in CI. (Status: *Pending execution in CI pipeline*).

---

### Unit Testing Specifications & Fixtures

```
+----------------------------------------------------------------------------------------------------------------+
|                                        PLANNED UNIT TEST SPECIFICATIONS                                        |
+-------------------+----------------------------+-----------------------------+---------------------------------+
| Test Identifier   | Test Target                | Module Under Test           | Input / Expected Assertion      |
+-------------------+----------------------------+-----------------------------+---------------------------------+
| `test_parser_01`  | Valid PR URL syntax        | `app.github.parser`         | Input: github.com/nodejs/node/  |
|                   |                            |                             | pull/41749 -> target.number=41749|
| `test_parser_02`  | Malformed URL rejection    | `app.github.parser`         | Input: not-a-url -> raises      |
|                   |                            |                             | `InvalidGitHubURLException`     |
| `test_cleaner_01` | Bot comment filtering      | `app.preprocessing.cleaner` | Filter author "dependabot[bot]" |
|                   |                            |                             | -> comment omitted from output  |
| `test_budget_01`  | Chronological chunking     | `app.preprocessing.budgeter`| Thread > 12k tokens -> records  |
|                   |                            |                             | `was_truncated: true`           |
| `test_verify_01`  | Level 1 link verification  | `app.ai.verifier`           | ID "1034981" exists in thread   |
|                   |                            |                             | -> `is_technically_verified=True|
| `test_verify_02`  | Stripping fabricated ID    | `app.ai.verifier`           | ID "999999" not in thread       |
|                   |                            |                             | -> stripped from evidence_ids   |
| `test_madr_01`    | MADR markdown generation   | `app.adr.compiler`          | Renders valid MADR 3.0.0 table  |
+-------------------+----------------------------+-----------------------------+---------------------------------+
```

#### Sample Unit Test Code

```python
# backend/tests/unit/test_verifier.py
import pytest
from datetime import datetime
from app.domain.schemas import ConsideredOption, OptionStatus
from app.ai.verifier import verify_technical_evidence
from app.domain.entities import CanonicalDiscussionComment, CommentType

def test_verifier_preserves_valid_and_strips_hallucinated_ids():
    # Setup valid comments in thread
    comments = [
        CanonicalDiscussionComment(
            id="101",
            comment_type=CommentType.CONVERSATION,
            author="alice",
            author_association="MEMBER",
            body="We should adopt Undici for performance.",
            created_at=datetime.utcnow(),
            html_url="https://github.com/org/repo/pull/1#issuecomment-101"
        )
    ]
    
    # Options: one valid ID ("101"), one hallucinated ID ("999")
    options = [
        ConsideredOption(name="Undici", status=OptionStatus.CHOSEN, evidence_ids=["101"]),
        ConsideredOption(name="node-fetch", status=OptionStatus.REJECTED, rejection_reason="Spec divergence", evidence_ids=["999"])
    ]
    
    verified_catalog, updated_options = verify_technical_evidence(options, comments)
    
    # Assertions
    assert len(verified_catalog) == 1
    assert verified_catalog[0].comment_id == "101"
    assert verified_catalog[0].is_technically_verified is True
    
    # The hallucinated ID 999 must be stripped from evidence_ids
    assert updated_options[0].evidence_ids == ["101"]
    assert updated_options[1].evidence_ids == []
```

---

### Integration Testing Specifications

- **`test_github_client_live_or_mock`:** Verifies that `GitHubClient` correctly parses JSON responses and traverses pagination headers using `respx` mock fixtures.
- **`test_ollama_json_schema`:** Queries the local Ollama instance with Prompt 2 and verifies that the output conforms strictly to `DecisionPayload`.
- **`test_end_to_end_cli`:** Invokes `cli.py` with the pre-recorded fixture `examples/sample_input.json` and verifies that the output MADR document matches `examples/0001-sample-output.md`.

---

### Failure & Resilience Testing Specifications

- **Rate Limit Exhaustion:** Simulate HTTP 403 with `x-ratelimit-remaining: 0`. Verify that client raises `GitHubRateLimitExceededException` with reset time.
- **Non-Decision Discussion:** Feed a routine typo patch thread. Verify that Stage 1 classifier returns `is_decision: false` and no MADR is compiled.
- **Ollama Offline:** Simulate `httpx.ConnectError` on port 11434. Verify that the CLI outputs a clean message instructing the user to run `ollama serve`.

---

## 9. Quantitative & Qualitative Evaluation Metrics

```
+---------------------------------------------------------------------------------------------------------------+
|                                      SYSTEM EVALUATION METRICS MATRIX                                         |
+--------------------------------+--------------------+---------------------+-----------------------------------+
| Metric Name                    | Formula / Method   | Target Threshold    | Evaluation Method                 |
+--------------------------------+--------------------+---------------------+-----------------------------------+
| Decision Detection Precision   | TP / (TP + FP)     | >= 90% (Planned)    | Tested against 20 known issues    |
| Decision Detection Recall      | TP / (TP + FN)     | >= 85% (Planned)    | (10 decisions, 10 non-decisions)  |
| Level 1 Evidence Verification  | Verified / Total   | 100% (Planned)      | Automated ID validator            |
| Schema Validation Success Rate | Valid / Total Runs | 100% (Planned)      | Pydantic parse failure counter    |
| End-to-End Inference Latency   | Ingest to MADR     | PENDING (Bench)     | Benchmark on target test machine  |
+--------------------------------+--------------------+---------------------+-----------------------------------+
```

### Manual Qualitative Evaluation Protocol
For hackathon evaluation without a large labeled corpus:
1. Select 10 diverse public GitHub discussions (5 significant decision PRs, 5 routine bug fixes/chores).
2. Execute Primordial on each thread.
3. Manually inspect:
   - Did the classifier correctly distinguish decision vs. non-decision?
   - Are the extracted rejected alternatives genuinely grounded in the comments?
   - Do the permalinks open the exact relevant comment on GitHub?

---

## 10. Security, Privacy, and Token Reliability Controls

1. **Zero Outbound Token Leakage:** The `GITHUB_TOKEN` is stored exclusively in the backend `.env` file. It is never exposed in frontend code, never transmitted over client HTTP headers, and never written to database tables.
2. **Read-Only Operations:** Primordial possesses no API methods for creating or modifying issues, PRs, or comments on external repositories.
3. **Prompt Injection Mitigation:** Discussion comments are treated as untrusted text and isolated within `<transcript>` XML tags. System instructions explicitly prohibit executing commands embedded inside comment bodies.
4. **Markdown Sanitization:** Rendered Markdown in the web dashboard is sanitized to prevent Cross-Site Scripting (XSS).

---

## 11. 12-Stage Phased Implementation Roadmap

```
+---------------------------------------------------------------------------------------------------------------+
|                                    12-STAGE PHASED IMPLEMENTATION ROADMAP                                     |
+----+--------------------------+-------+-----------------------+---------------------+-------------------------+
| #  | Milestone Name           | Phase | Deliverable           | Responsible Member  | Completion Criteria     |
+----+--------------------------+-------+-----------------------+---------------------+-------------------------+
| 01 | Project Skeleton & CI    | 1     | Repo, Pytest, env     | Prince Chhikara     | CI runs cleanly on push |
| 02 | GitHub REST Client       | 1     | Parser & httpx client | Prince Chhikara     | Ingests PR #41749       |
| 03 | Preprocessing Pipeline   | 1     | Cleaner & Budgeter    | Prince Chhikara     | Chronological chunking  |
| 04 | Ollama Service Connector | 1     | Ollama HTTP Client    | Shaurya Negi        | Returns JSON from model |
| 05 | Stage 1 Decision Gate    | 1     | Binary Classifier     | Shaurya Negi        | Passes bug fix control  |
| 06 | Stage 2 Structured Extr. | 1     | Structured Extractor  | Shaurya Negi        | Canonical schema output |
| 07 | Level 1 Evidence Verifier| 1     | Citation Verifier     | Shaurya Negi        | Rejects fake comment IDs|
| 08 | MADR 3.0.0 Compiler      | 1     | Jinja2 Generator      | Manisha Jain        | Generates standard MADR |
| 09 | Primordial CLI Wrapper   | 1     | `cli.py` Entrypoint   | Prince Chhikara     | Full CLI demo working   |
| 10 | FastAPI Service & Storage| 2     | Web API & SQLite WAL  | Prince Chhikara     | POST /api/v1/extract    |
| 11 | React Web Dashboard      | 3     | Single-page UI        | Manisha Jain        | Dual-pane view renders  |
| 12 | End-to-End Test & Rehear.| 1-3   | Live Demo Rehearsal   | All Team Members    | 3 clean demo traces     |
+----+--------------------------+-------+-----------------------+---------------------+-------------------------+
```

---

## 12. Team Work Division & Integration Contracts

```
+-------------------------------------------------------------------------------------------------------------+
|                                        TEAM RESPONSIBILITY MATRIX                                           |
+---------------------+------------------------------+--------------------------------------------------------+
| Member Name         | Functional Ownership         | Core Deliverables & Integration Contracts              |
+---------------------+------------------------------+--------------------------------------------------------+
| **Prince Chhikara** | **Backend Infrastructure &** | 1. `app.github.*`: URL Parser & Async REST API Client  |
|                     | **Data Engineering**         | 2. `app.preprocessing.*`: Cleaner & Context Budgeter   |
|                     |                              | 3. `app.cli.py`: Phase 1 CLI executable                |
|                     |                              | 4. `app.storage.*`: SQLite WAL database & FTS5 search  |
|                     |                              | 5. `app.main.py`: FastAPI application (Phase 2)        |
|                     |                              | *Contract:* Delivers `CleanedDiscussionThread` to AI   |
+---------------------+------------------------------+--------------------------------------------------------+
| **Shaurya Negi**    | **AI / NLP Intelligence &**  | 1. `app.ai.ollama_client`: Local Ollama JSON connector |
|                     | **Verification Engine**      | 2. `app.ai.prompts`: Production prompt engineering     |
|                     |                              | 3. `app.ai.classifier`: Binary decision gate (Stage 1) |
|                     |                              | 4. `app.ai.extractor`: Structured extractor (Stage 2)  |
|                     |                              | 5. `app.ai.verifier`: Level 1 evidence verifier        |
|                     |                              | *Contract:* Delivers `VerifiedDecisionResponse` to ADR |
+---------------------+------------------------------+--------------------------------------------------------+
| **Manisha Jain**    | **Frontend Dashboard &**     | 1. `app.adr.compiler`: MADR 3.0.0 Jinja2 generator     |
|                     | **ADR Presentation Layer**   | 2. `frontend/src/*`: React SPA, Vite, Tailwind (Phase 3)|
|                     |                              | 3. Dual-Pane UI: MADR preview & Evidence Drawer cards   |
|                     |                              | 4. `examples/`: Sample inputs and actual outputs       |
|                     |                              | *Contract:* Consumes `POST /api/v1/extract` response   |
+---------------------+------------------------------+--------------------------------------------------------+
```

---

## 13. Live Hackathon Demonstration Plan & Script

### Demonstration Overview
- **Duration:** 5 Minutes.
- **Presenter:** Primordial Team.
- **Target Repo & PR:** `https://github.com/nodejs/node/pull/41749` (Node.js Built-in Fetch API).
- **Negative Control Target:** A closed routine bug fix issue.

### Step-by-Step Demo Script for Judges

1. **Minute 0:00 – 1:00 (The Problem Pitch):**
   - *"Judges, open-source teams make critical architectural decisions in GitHub PRs and issues. While code is merged, the reasoning, trade-offs, and rejected options get buried under thousands of newer issues. Look at Node.js PR #41749: 112 comments debating Web Fetch API, undici, and node-fetch. A new contributor trying to understand why node-fetch was rejected has to spend 45 minutes digging through comments."*
2. **Minute 1:00 – 2:00 (Live Execution):**
   - Run the command via CLI (or Web Dashboard in Phase 3):
     ```bash
     primordial extract https://github.com/nodejs/node/pull/41749 --output docs/adr/0001-fetch.md
     ```
   - Explain what is happening:
     - Ingesting PR description, conversation comments, and inline review comments via GitHub REST API.
     - Stripping automated bot messages and CI logs.
     - Running local open-weight model (`qwen2.5:7b` via Ollama) with zero cloud API costs.
3. **Minute 2:00 – 3:30 (Recovered Decision & Evidence Verification):**
   - Present the compiled MADR 3.0.0 document:
     - Title, Status: Accepted, Decision Drivers, and Pros/Cons.
     - Highlight the rejected alternative: *"Bundle community node-fetch — Rejected due to WHATWG spec divergence."*
     - Point to the Level 1 Technical Verification Log: permalinks verified directly against authentic comment IDs.
4. **Minute 3:30 – 4:15 (Negative Control Demonstration):**
   - *"What happens if an issue is just a routine typo fix or bug report?"*
   - Run Primordial on a routine bug report issue.
   - Show early termination: *"No Architectural Decision Detected in this thread."*
   - *"Notice that Primordial refuses to hallucinate a false decision record."*
5. **Minute 4:15 – 5:00 (Architecture & Q&A):**
   - Summarize key differentiators: Local open-weight execution via Ollama, synchronous modular monolith, Level 1 technical evidence verification, and MADR 3.0.0 compliance.

---

## 14. Engineering Risks, Trade-Offs, and Mitigations

```
+----------------------------------------------------------------------------------------------------------------+
|                                    RISK AND TRADE-OFF MITIGATION MATRIX                                        |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| Risk Description        | Severity    | Primary Impact                     | Proactive Mitigation              |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| Local LLM OOM / Crash   | Critical    | Inference fails during demo        | Quantize to q4_K_M (~4.7 GB);     |
|                         |             |                                    | pre-warm model in memory          |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| Venue Wi-Fi Failure     | Critical    | GitHub API unreachable             | Pre-load offline JSON fixtures;   |
|                         |             |                                    | pass via `--fixture` CLI argument |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| GitHub Rate Limit Hit   | High        | Ingestion blocked on judge machine | Read GITHUB_TOKEN from .env;      |
|                         |             |                                    | increases limit to 5,000 req/hr   |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| Long Context Ceiling    | Medium      | Model ignores comments in middle   | Chronological chunking with       |
|                         |             | of 100-comment thread              | explicit truncation reporting     |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| Model Hallucinates URL  | High        | Broken citation links in ADR       | Permalinks generated by Python,   |
|                         |             |                                    | NOT by the language model         |
+-------------------------+-------------+------------------------------------+-----------------------------------+
| React Toolchain Issues  | Medium      | Web UI fails to build at hackathon | CLI-first MVP architecture;       |
|                         |             |                                    | single-file HTML5 fallback        |
+-------------------------+-------------+------------------------------------+-----------------------------------+
```

---

## 15. Future Roadmap & Beyond-MVP Horizons

Following the Hacktoberfest hackathon, Primordial will expand from single-thread recovery to an autonomous repository intelligence platform:

1. **Asynchronous Job Queue & Status Polling:** Celery/Redis background task execution with `/jobs/{id}` polling endpoints for very large multi-hundred-comment discussions.
2. **GitHub Discussions GraphQL Ingestion:** Ingesting multi-threaded community discussions and Q&A boards using GitHub's GraphQL API v4.
3. **Full-Repository Automated Decision Mining:** Background crawler capable of ingesting historical issues and pull requests across an entire repository.
4. **Decision Knowledge Graph:** Modeling inter-decision relationships (e.g., *"ADR 0014 supersedes ADR 0003"*).
5. **Autonomous Pull Request Impact Radar (GitHub Action):** A CI bot that monitors incoming PRs and alerts authors: *"Warning: This PR proposes an architecture that was evaluated and rejected in ADR 0008."*
6. **Dense Vector RAG Retrieval:** Semantic embeddings (e.g., BGE-large) enabling conceptual search across hundreds of recovered ADRs.

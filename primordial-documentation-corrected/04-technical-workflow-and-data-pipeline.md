# Primordial: Technical Workflow and Data Pipeline (Corrected)

**Document Identifier:** `PRIMORDIAL-DOC-04-REV2`  
**Project:** Primordial — Open Source Decision Intelligence and Knowledge Recovery  
**Repository:** `primordial-hacktoberfest`  
**Team Members:** Shaurya Negi, Prince Chhikara, Manisha Jain  
**Hackathon:** Hacktoberfest 2026 – Hack Day Sonipat  
**Institution:** Newton School of Technology, Rishihood University  
**Problem Statement:** Problem Statement 06 — Open Source Decision Intelligence and Knowledge Recovery  
**Documentation Version:** 2.0.0 (Implementation-Ready Revision)

---

## Table of Contents

1. [Pipeline Architectural Overview](#1-pipeline-architectural-overview)
2. [Stage-by-Stage Engineering Specification](#2-stage-by-stage-engineering-specification)
   - [Stage 1: URL Parsing and Syntax Validation](#stage-1-url-parsing-and-syntax-validation)
   - [Stage 2: Entity Routing (Issue vs. Pull Request)](#stage-2-entity-routing-issue-vs-pull-request)
   - [Stage 3: GitHub API Ingestion & Rate-Limit Inspection](#stage-3-github-api-ingestion--rate-limit-inspection)
   - [Stage 4: Data Normalization & Canonical Modeling](#stage-4-data-normalization--canonical-modeling)
   - [Stage 5: Discourse Preprocessing & Noise Elimination](#stage-5-discourse-preprocessing--noise-elimination)
   - [Stage 6: Context Budgeting & Chronological Chunking](#stage-6-context-budgeting--chronological-chunking)
   - [Stage 7: AI Stage 1 — Decision Relevance Classification](#stage-7-ai-stage-1--decision-relevance-classification)
   - [Stage 8: AI Stage 2 — Structured Rationale Extraction](#stage-8-ai-stage-2--structured-rationale-extraction)
   - [Stage 9: Pydantic Schema Validation & Repair](#stage-9-pydantic-schema-validation--repair)
   - [Stage 10: Two-Level Evidence Verification (Level 1 Automated)](#stage-10-two-level-evidence-verification-level-1-automated)
   - [Stage 11: MADR 3.0.0 Document Compilation](#stage-11-madr-300-document-compilation)
   - [Stage 12: Output & Persistence (CLI & Phase 2 SQLite)](#stage-12-output--persistence-cli--phase-2-sqlite)
3. [AI Processing Pipeline & Anti-Hallucination Safeguards](#3-ai-processing-pipeline--anti-hallucination-safeguards)
   - [Safeguard 1: Strict Binary Decision Gate](#safeguard-1-strict-binary-decision-gate)
   - [Safeguard 2: Anti-Confabulation Instructions & Mandatory Nulls](#safeguard-2-anti-confabulation-instructions--mandatory-nulls)
   - [Safeguard 3: Deterministic Link Generation by Python, Not AI](#safeguard-3-deterministic-link-generation-by-python-not-ai)
   - [Safeguard 4: Schema-Constrained Decoding (Ollama JSON Mode)](#safeguard-4-schema-constrained-decoding-ollama-json-mode)
   - [Safeguard 5: Truncation Reporting & Provenance Transparency](#safeguard-5-truncation-reporting--provenance-transparency)
4. [Canonical Data Payload Example](#4-canonical-data-payload-example)
5. [Error Handling, Fallback, and Recovery Matrix](#5-error-handling-fallback-and-recovery-matrix)

---

## 1. Pipeline Architectural Overview

The Primordial data pipeline processes unstructured GitHub collaboration data through a deterministic twelve-stage linear workflow.

To ensure execution stability during the hackathon, the pipeline runs as a **synchronous modular monolith** in Python 3.11+ using `FastAPI`, `httpx`, `Pydantic v2`, and `Ollama`. 

In Phase 1, the pipeline is invoked directly via the CLI (`primordial extract <url>`). In Phase 2, the exact same pipeline is exposed over HTTP via `POST /api/v1/extract`.

```
+-------------------------------------------------------------------------------------------------------------+
|                                  PRIMORDIAL DATA PIPELINE SEQUENCE                                          |
+-------------------------------------------------------------------------------------------------------------+

  [ Raw GitHub URL ]
         |
         v
  (Stage 1) URL Validation & Regex Parsing  --------------> [Invalid URL Exception -> Error / 400 Bad Request]
         |
         v
  (Stage 2) Entity Identification & Routing (Issue vs PR)
         |
         v
  (Stage 3) GitHub REST API Client (Pagination & Rate Checks)
            - Fetch Issue/PR metadata and description
            - Fetch conversation comments
            - Fetch review comments (PR only)
            - Fetch review summaries (PR only)
         |
         v
  (Stage 4) Data Normalization (Convert to CanonicalDiscussionComment)
         |
         v
  (Stage 5) Discourse Preprocessing (Filter bots, clean noise, preserve code blocks)
         |
         v
  (Stage 6) Context Budgeting & Chronological Chunking (Report truncation if needed)
         |
         v
  (Stage 7) AI Stage 1: Binary Decision Classifier (Candidate: Qwen 2.5 7B via Ollama)
            * If is_decision == False -------------------> [Early Return: Non-Decision Summary]
         |
         v
  (Stage 8) AI Stage 2: Structured Rationale Extraction (Ollama JSON Mode)
         |
         v
  (Stage 9) Pydantic Schema Validation & JSON Repair
         |
         v
  (Stage 10) Level 1 Technical Evidence Verification (Comment ID & Permalink Matcher)
         |
         v
  (Stage 11) MADR 3.0.0 Markdown Document Compilation
         |
         v
  (Stage 12) Output Generation (CLI stdout/files; Phase 2 SQLite WAL Persistence)
```

---

## 2. Stage-by-Stage Engineering Specification

---

### Stage 1: URL Parsing and Syntax Validation

- **Responsible Module:** `backend.app.github.parser`
- **Input:** Raw user-provided string `raw_url` (from CLI parameter or API request body).
- **Processing:**
  1. Trim leading/trailing whitespace.
  2. Match against canonical GitHub URL regular expression:
     ```python
     GITHUB_URL_REGEX = re.compile(
         r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)/(?P<type>issues|pull)/(?P<number>\d+)$"
     )
     ```
  3. Extract named capture groups: `owner`, `repo`, `type`, `number`.
- **Output:** Validated `GitHubTarget` dataclass:
  ```python
  GitHubTarget(owner="nodejs", repo="node", entity_type="pull", entity_number=41749)
  ```
- **Validation Rules:** URL must point to `github.com` and contain a valid entity type (`issues` or `pull`) with integer ID.
- **Possible Errors:**
  - `InvalidGitHubURLException`: Thrown if regex fails. Returns error exit code in CLI or HTTP 400 in API.

---

### Stage 2: Entity Routing (Issue vs. Pull Request)

- **Responsible Module:** `backend.app.github.router`
- **Input:** `GitHubTarget` object.
- **Processing:**
  - Evaluates `target.entity_type`:
    - If `entity_type == "pull"`, activates `PullRequestStrategy`.
    - If `entity_type == "issues"`, activates `IssueStrategy`.
- **Output:** Configured API execution plan specifying which endpoints to query.
- **Validation Rules:** Prevents calling PR-specific review endpoints on standard issues, avoiding unnecessary HTTP 404/410 errors.
- **Possible Errors:** None (deterministic routing).

---

### Stage 3: GitHub API Ingestion & Rate-Limit Inspection

- **Responsible Module:** `backend.app.github.client`
- **Input:** `GitHubTarget` and execution plan.
- **Processing:**
  1. Configures `httpx.AsyncClient` with standard headers:
     ```python
     headers = {
         "Accept": "application/vnd.github.v3+json",
         "User-Agent": "Primordial-Decision-Intelligence/2.0"
     }
     if token := os.getenv("GITHUB_TOKEN"):
         headers["Authorization"] = f"Bearer {token}"
     ```
  2. Inspects `x-ratelimit-remaining` on each response. If remaining requests drop to 0, raises `GitHubRateLimitExceededException` with the epoch reset timestamp.
  3. **Data Fetching:**
     - **For Issues:**
       - `GET /repos/{owner}/{repo}/issues/{number}` (Metadata and description).
       - `GET /repos/{owner}/{repo}/issues/{number}/comments?per_page=100` (Conversation comments; traverses `Link` headers up to 250 comments).
     - **For Pull Requests:**
       - `GET /repos/{owner}/{repo}/pulls/{number}` (Metadata and description).
       - `GET /repos/{owner}/{repo}/issues/{number}/comments?per_page=100` (Conversation comments).
       - `GET /repos/{owner}/{repo}/pulls/{number}/comments?per_page=100` (Inline review diff comments).
       - `GET /repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100` (Review status summaries).
- **Output:** Raw dictionary containing `metadata`, `conversation_comments`, `review_comments`, and `reviews`.
- **Validation Rules:** Maximum pagination limit capped at 250 comments to prevent timeout on very large threads.
- **Possible Errors:**
  - `GitHubRateLimitExceededException`: HTTP 403 with `x-ratelimit-remaining: 0`.
  - `GitHubResourceNotFoundException`: HTTP 404 (private or nonexistent repo).
  - `httpx.TimeoutException`: Exceeded 15-second per-request timeout.

---

### Stage 4: Data Normalization & Canonical Modeling

- **Responsible Module:** `backend.app.github.normalizer`
- **Input:** Raw JSON arrays from disparate GitHub endpoints.
- **Processing:**
  Transforms heterogeneous comments into a unified, chronologically ordered sequence of `CanonicalDiscussionComment` objects:
  ```python
  class CommentType(str, Enum):
      DESCRIPTION = "description"
      CONVERSATION = "conversation"
      REVIEW_COMMENT = "review_comment"
      REVIEW_SUMMARY = "review_summary"

  class CanonicalDiscussionComment(BaseModel):
      id: str
      comment_type: CommentType
      author: str
      author_association: str  # OWNER, MEMBER, COLLABORATOR, CONTRIBUTOR, NONE
      body: str
      created_at: datetime
      html_url: str
      diff_hunk: Optional[str] = None
      path: Optional[str] = None
      in_reply_to_id: Optional[str] = None
  ```
  - Prepends the original Issue/PR description as comment ID `"0"`.
  - Sorts all comments chronologically by `created_at`.
- **Output:** `CanonicalDiscussionThread` object.
- **Validation Rules:** Every comment must have a non-empty ID, author handle, and body text.
- **Possible Errors:** `DataNormalizationError` if critical fields are absent.

---

### Stage 5: Discourse Preprocessing & Noise Elimination

- **Responsible Module:** `backend.app.preprocessing.cleaner`
- **Input:** `CanonicalDiscussionThread`.
- **Processing:**
  Applies filtering passes:
  1. *Bot Filtering:* Drops comments where author login ends in `[bot]` or matches `BOT_BLOCKLIST` (`"dependabot"`, `"codecov"`, `"stale"`, `"github-actions"`).
  2. *Noise Filtering:* Drops comments shorter than 5 characters containing only whitespace or reaction emojis (`+1`, `:heart:`).
  3. *Boilerplate Removal:* Strips automated CI tables (e.g., `"Coverage report: 85%"`), lockfile diff notifications, and mobile signatures (`"Sent from my mobile"`).
  4. *Technical Substance Protection:* Verbatim preservation of markdown code blocks (```` ```...``` ````), inline backticks, file diff references, author handles, and comment IDs.
- **Output:** `CleanedDiscussionThread` containing only substantive human engineering contributions.
- **Validation Rules:** If all comments are filtered out, flags `is_empty = True`.
- **Possible Errors:** None.

---

### Stage 6: Context Budgeting & Chronological Chunking

- **Responsible Module:** `backend.app.preprocessing.budgeter`
- **Input:** `CleanedDiscussionThread`.
- **Processing:**
  1. Estimates token count using a conservative character-to-token ratio (1 word ≈ 1.33 tokens; 4 characters ≈ 1 token).
  2. Target budget ceiling: **12,000 tokens** (safe for 16k context window).
  3. **Chronological Chunking Algorithm:**
     - The issue/PR description (ID `"0"`) is **always preserved** at the beginning of the context.
     - If total tokens <= 12,000: The entire thread is formatted as a single chronological transcript.
     - If total tokens > 12,000:
       - The conversation is divided into chronological chunks with a 2-comment overlap between adjacent chunks.
       - Comments containing decision markers (e.g., *"propose"*, *"alternative"*, *"benchmark"*, *"reject"*, *"consequence"*, *"trade-off"*) and comments by `OWNER` or `MEMBER` maintainers are preserved with priority without breaking chronological sequence.
       - Reply relationships (`in_reply_to_id`) are preserved together where possible.
       - Populates `ContextProcessingMetadata`:
         ```python
         was_truncated = True
         processing_note = f"Discussion exceeded token ceiling. Processed {retained_count} of {total_count} comments using chronological chunking."
         ```
  4. Formats each comment with an explicit citation header:
     ```text
     [COMMENT ID: 1034981 | AUTHOR: @mcollina (MEMBER) | DATE: 2022-02-03]
     Undici is 3x faster than node-fetch and strictly aligns with the standard.
     ```
- **Output:** Formatted transcript string and `ContextProcessingMetadata`.
- **Validation Rules:** Never exceed the model's configured context window. Never silently omit comments without recording `was_truncated: true`.
- **Possible Errors:** `ContextOverflowError` if a single comment exceeds the entire budget.

---

### Stage 7: AI Stage 1 — Decision Relevance Classification

- **Responsible Module:** `backend.app.ai.classifier`
- **Input:** Formatted transcript string and repository metadata.
- **Processing:**
  1. Constructs the binary classification prompt instructing the model to act as a Software Architect.
  2. Invokes Ollama API (`POST http://localhost:11434/api/generate` or `/api/chat`) with `model="qwen2.5:7b"` and `format="json"`.
  3. Model evaluates whether the thread contains an architectural/technical decision versus routine maintenance.
  4. Parses response into Pydantic model:
     ```python
     class ClassificationResult(BaseModel):
         is_decision: bool
         confidence_score: float  # Heuristic score between 0.0 and 1.0 (not a calibrated probability)
         reasoning: str
     ```
  5. *Branching:*
     - If `is_decision == False`: Pipeline terminates early, returns non-decision summary, and avoids fabricating an ADR.
     - If `is_decision == True`: Passes transcript to Stage 8.
- **Output:** `ClassificationResult`.
- **Validation Rules:** `confidence_score` must be between 0.0 and 1.0.
- **Possible Errors:**
  - `OllamaConnectionError`: Ollama daemon offline.
  - `ClassificationJSONParseError`: Model failed to output valid JSON.

---

### Stage 8: AI Stage 2 — Structured Rationale Extraction

- **Responsible Module:** `backend.app.ai.extractor`
- **Input:** Formatted transcript string, metadata, and classification reasoning.
- **Processing:**
  1. Injects transcript into the Structured Extraction Prompt.
  2. Calls Ollama with `format="json"`:
     - Enforces extraction of: `title`, `status`, `context_and_problem`, `decision_drivers`, `chosen_option`, `considered_options`, `consequences`, and cited comment IDs.
     - Strict anti-hallucination instruction: **"Every option must cite an authentic COMMENT ID from the transcript. If rejection rationale was not stated, write null. Do not invent missing options."**
  3. Awaits JSON response.
- **Output:** Raw JSON string.
- **Validation Rules:** Output must contain required canonical JSON keys.
- **Possible Errors:**
  - `ModelInferenceTimeout`: Exceeded 90-second timeout.
  - `IncompleteJSONResponse`: Generation was truncated by token limit.

---

### Stage 9: Pydantic Schema Validation & Repair

- **Responsible Module:** `backend.app.ai.validator`
- **Input:** Raw JSON string from Stage 8.
- **Processing:**
  1. Executes `json.loads()`.
  2. If JSON contains minor trailing syntax errors, passes text through a lightweight repair balancer.
  3. Validates against `DecisionPayload` Pydantic model:
     - Enforces nullable `chosen_option` when `status != "accepted"`.
     - Validates that `status` belongs to `DecisionStatus` enum.
- **Output:** Validated `DecisionPayload` object.
- **Validation Rules:** Must pass Pydantic validation cleanly.
- **Possible Errors:** `SchemaValidationException` if required fields are missing.

---

### Stage 10: Two-Level Evidence Verification (Level 1 Automated)

- **Responsible Module:** `backend.app.ai.verifier`
- **Input:** `DecisionPayload` and original `CanonicalDiscussionThread`.
- **Processing:**
  1. Builds a lookup index of all real comment IDs from the fetched GitHub data:
     ```python
     valid_comment_map = {str(c.id): c for c in thread.comments}
     ```
  2. Iterates over all cited `evidence_ids` in options and claims:
     - **Level 1 Technical Verification:**
       - If `evidence_id in valid_comment_map`:
         - Comment physically exists.
         - Extracts authentic author, timestamp, and permalink (`html_url`).
         - Verifies whether `verbatim_excerpt` matches the comment body.
         - Populates `EvidenceItem` with `is_technically_verified = True`.
       - If `evidence_id not in valid_comment_map`:
         - The AI cited a nonexistent comment ID.
         - Strips the invalid ID from the option's citation list and logs a warning.
  3. **Level 2 Semantic Verification:**
     - The system notes that verifying semantic entailment (whether the quote actually proves the claim) requires human maintainer review. The automated pipeline does not claim 100% semantic correctness.
- **Output:** `List[EvidenceItem]` and cleaned `DecisionPayload`.
- **Validation Rules:** Never display a fabricated comment ID or broken permalink.
- **Possible Errors:** None (fault-tolerant verification).

---

### Stage 11: MADR 3.0.0 Document Compilation

- **Responsible Module:** `backend.app.adr.compiler`
- **Input:** Validated `DecisionPayload`, `List[EvidenceItem]`, and target metadata.
- **Processing:**
  1. Assigns decision number (e.g., `0001` or sequential counter).
  2. Generates slugified filename: `{number}-{slug}.md`.
  3. Compiles the standardized MADR 3.0.0 Jinja2 template:
     - Header block (`Status`, `Date`, `Deciders`, `Source Discussion`).
     - `## Context and Problem Statement`
     - `## Decision Drivers`
     - `## Considered Options`
     - `## Decision Outcome`
     - `## Pros and Cons of the Options`
     - `## Evidence & Verification Log (Level 1 Technical Verification)` (Table with direct permalinks).
- **Output:** Formatted CommonMark string.
- **Validation Rules:** Must be valid GitHub Flavored Markdown (GFM).
- **Possible Errors:** None.

---

### Stage 12: Output & Persistence (CLI & Phase 2 SQLite)

- **Responsible Module:** `backend.app.cli` (Phase 1) / `backend.app.storage.repository` (Phase 2)
- **Input:** Complete `VerifiedDecisionResponse` and MADR string.
- **Processing:**
  - **In Phase 1 (CLI):**
    - Prints formatted Markdown or canonical JSON to terminal stdout.
    - Writes `.md` or `.json` file to `--output` path if specified.
  - **In Phase 2 (FastAPI & SQLite):**
    - Persists record into `primordial.db` (SQLite in WAL mode).
    - Updates SQLite FTS5 full-text virtual index.
    - Returns JSON response envelope with HTTP 200.
- **Output:** File saved or database row ID returned.
- **Validation Rules:** Database write must execute atomically.
- **Possible Errors:** `SQLiteDatabaseError` (disk full, lock timeout).

---

## 3. AI Processing Pipeline & Anti-Hallucination Safeguards

Generative language models can introduce ungrounded claims, invent alternatives, or hallucinate URLs. Primordial implements five explicit engineering safeguards:

### Safeguard 1: Strict Binary Decision Gate
Stage 7 enforces a binary classification filter. If an issue is purely a routine bug fix, documentation patch, or an unresolved debate where maintainers reached no consensus, the pipeline exits early. It outputs an informational summary rather than fabricating a false decision record.

### Safeguard 2: Anti-Confabulation Instructions & Mandatory Nulls
Prompts explicitly forbid guessing unstated facts:
- *"Do not invent alternatives. Only include an option if a participant explicitly discussed it in the transcript."*
- *"If the discussion does not state why an alternative was rejected, set rejection_reason to null. Do not deduce unmentioned reasons."*
- If the thread lacks a clear accepted decision, `status` is set to `"proposed"` or `"insufficient_evidence"`, and `chosen_option` is set to `null`.

### Safeguard 3: Deterministic Link Generation by Python, Not AI
The language model is **never** permitted to generate URLs. The model is only asked to extract the integer `comment_id`. The Python backend then deterministically constructs the canonical permalink:
- Issue comment: `https://github.com/{owner}/{repo}/issues/{n}#issuecomment-{id}`
- Review comment: `https://github.com/{owner}/{repo}/pull/{n}#discussion_r{id}`

### Safeguard 4: Schema-Constrained Decoding (Ollama JSON Mode)
The backend invokes Ollama with `format="json"`. This constrains token decoding to valid JSON tokens, eliminating markdown conversational wrappers (`"Here is the JSON..."`) and guaranteeing parseable syntax.

### Safeguard 5: Truncation Reporting & Provenance Transparency
If a discussion exceeds 12,000 tokens, Primordial reports the exact truncation status in `context_metadata`. The system never claims that all comments were analyzed if some were omitted due to token budgets.

---

## 4. Canonical Data Payload Example

Every stage produces or consumes data conforming to this canonical structure:

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

## 5. Error Handling, Fallback, and Recovery Matrix

```
+------------------------------------------------------------------------------------------------------------------+
|                                    PIPELINE ERROR HANDLING AND RECOVERY MATRIX                                   |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Pipeline Stage           | Potential Failure     | Catching Exception               | Recovery / Fallback Action |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 1: URL Parsing     | Malformed URL string  | `InvalidGitHubURLException`      | Return error exit code /   |
|                          |                       |                                  | HTTP 400 with regex format |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 3: GitHub Fetch    | Rate limit exhausted  | `GitHubRateLimitExceededException| Return error with reset    |
|                          | (HTTP 403 / 429)      |                                  | timestamp; prompt for token|
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 3: GitHub Fetch    | Private/deleted repo  | `GitHubResourceNotFoundException`| Return error; prompt user  |
|                          | (HTTP 404)            |                                  | to verify repo visibility  |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 5: Preprocessing   | Thread contains only  | `EmptyDiscussionException`       | Return informational exit  |
|                          | bot spam or is empty  |                                  | "Thread contains no human  |
|                          |                       |                                  | technical discourse"       |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 7/8: AI Inference  | Ollama service not    | `httpx.ConnectError`             | Prompt user to run         |
|                          | running / unreachable |                                  | `ollama serve`; exit       |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 7/8: AI Inference  | Inference timeout     | `httpx.ReadTimeout` (>90s)       | Re-attempt with aggressive |
|                          |                       |                                  | token truncation (last 10) |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 9: JSON Validation | Model outputs broken  | `json.JSONDecodeError`           | Run JSON brace repair; if  |
|                          | quotes or syntax      |                                  | unrecoverable, return err  |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 10: Evidence Check | Model cites a         | Missing ID detection             | Strip invalid citation;    |
|                          | nonexistent comment ID|                                  | keep claim with empty refs |
+--------------------------+-----------------------+----------------------------------+----------------------------+
| Stage 12: DB Persistence | SQLite file locked    | `sqlite3.OperationalError`       | Retry with WAL mode and    |
|                          |                       |                                  | 3-second backoff           |
+--------------------------+-----------------------+----------------------------------+----------------------------+
```

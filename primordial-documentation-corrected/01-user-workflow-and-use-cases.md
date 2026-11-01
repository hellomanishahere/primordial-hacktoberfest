# Primordial: User Workflow and Use Cases (Corrected)

**Document Identifier:** `PRIMORDIAL-DOC-01-REV2`  
**Project:** Primordial — Open Source Decision Intelligence and Knowledge Recovery  
**Repository:** `primordial-hacktoberfest`  
**Team Members:** Shaurya Negi, Prince Chhikara, Manisha Jain  
**Hackathon:** Hacktoberfest 2026 – Hack Day Sonipat  
**Institution:** Newton School of Technology, Rishihood University  
**Problem Statement:** Problem Statement 06 — Open Source Decision Intelligence and Knowledge Recovery  
**Documentation Version:** 2.0.0 (Implementation-Ready Revision)

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Target Users & Core Problems](#2-target-users--core-problems)
3. [User Personas](#3-user-personas)
   - [Persona 1: Aarav Patel — New Open-Source Contributor](#persona-1-aarav-patel--new-open-source-contributor)
   - [Persona 2: Dr. Elena Rostova — Core Repository Maintainer](#persona-2-dr-elena-rostova--core-repository-maintainer)
   - [Persona 3: Marcus Vance — Senior Software Engineer Joining an Existing Project](#persona-3-marcus-vance--senior-software-engineer-joining-an-existing-project)
4. [Phased Development & Interaction Strategy](#4-phased-development--interaction-strategy)
   - [Phase 1: Core Backend & CLI Workflow (MVP Core)](#phase-1-core-backend--cli-workflow-mvp-core)
   - [Phase 2: Backend API Service](#phase-2-backend-api-service)
   - [Phase 3: React Web Dashboard (Later Phase)](#phase-3-react-web-dashboard-later-phase)
5. [Complete User Journey (CLI & Web)](#5-complete-user-journey-cli--web)
   - [Text-Based User Journey Diagram](#text-based-user-journey-diagram)
6. [Step-by-Step Interaction Specifications](#6-step-by-step-interaction-specifications)
   - [CLI Interaction Flow](#cli-interaction-flow)
   - [Web Dashboard Interaction Flow](#web-dashboard-interaction-flow)
7. [Inputs and Outputs at Every Stage](#7-inputs-and-outputs-at-every-stage)
8. [Main User-Facing Features & MoSCoW Mapping](#8-main-user-facing-features--moscow-mapping)
9. [Error, Edge, and Empty States](#9-error-edge-and-empty-states)
10. [Detailed Illustrative Walkthrough: Node.js Built-in Fetch PR](#10-detailed-illustrative-walkthrough-nodejs-built-in-fetch-pr)
11. [Additional Real-World Use Cases](#11-additional-real-world-use-cases)

---

## 1. Product Overview

Primordial is an AI-powered Decision Intelligence and Knowledge Recovery platform designed for open-source software contributors, maintainers, and engineering teams.

In collaborative software projects, important architectural decisions are made organically inside distributed discussion threads—specifically GitHub Issues, Pull Request (PR) conversations, inline code reviews, and maintainer reviews. While Git version control faithfully preserves the resulting code changes, the *epistemic rationale*—the specific problem drivers, rejected alternatives, accepted trade-offs, and implementation constraints—rapidly gets buried under newer issues and PRs.

Primordial recovers this historical context. Given a public GitHub Issue or Pull Request URL, Primordial:
1. Ingests the discussion, including issue descriptions, conversation comments, inline review comments, and review summaries via the GitHub REST API.
2. Normalizes and cleans the discussion stream while preserving code snippets, author identities, timestamps, and comment anchors.
3. Analyzes the conversational discourse using an open-weight Large Language Model (candidate: Qwen 2.5 7B Instruct via Ollama).
4. Determines whether a technical or architectural decision exists.
5. Extracts a structured, multi-dimensional decision model (context, chosen option, rejected alternatives, trade-offs, and consequences).
6. Performs Level 1 technical evidence verification (verifying that cited comment IDs, authors, timestamps, and permalinks physically exist in the ingested thread).
7. Compiles a Markdown Architectural Decision Record conforming to the MADR 3.0.0 specification with direct permalinks to source comments.

---

## 2. Target Users & Core Problems

| User Group | Practical Pain Point | Current Manual Workaround | Real-World Impact |
|---|---|---|---|
| **New Contributors** | Submitting PRs with architectures already debated and rejected in earlier discussions. | Keyword searching GitHub issues; reading through dozens of unrelated threads. | Wasted implementation hours; contributor frustration and abandonment. |
| **Repository Maintainers** | Re-explaining settled architectural decisions repeatedly across release cycles. | Manually searching old closed issues from memory to paste links into comments. | Maintainer cognitive fatigue; less time spent reviewing novel PRs and shipping features. |
| **Engineers Onboarding to Existing Codebases** | Inability to understand *why* legacy modules have non-obvious constraints. | Running `git blame`, searching Slack archives, or interrupting senior engineers. | Slower onboarding; reluctance to refactor code due to fear of hidden regressions. |
| **Architects & Tech Leads** | Inability to maintain up-to-date Architectural Decision Records (ADRs) due to authoring friction. | Periodic ADR documentation sprints that are quickly abandoned under deadline pressure. | Architectural erosion; loss of institutional memory across staff transitions. |

---

## 3. User Personas

### Persona 1: Aarav Patel — New Open-Source Contributor
- **Role & Background:** 2nd-year Computer Science undergraduate, proficient in TypeScript and Python, active participant in Hacktoberfest.
- **Context:** Aarav wants to contribute to a major web framework repository (e.g., `nodejs/node` or `vercel/next.js`). He notices that an older HTTP utility could theoretically be replaced by an external modern library and considers writing a PR.
- **Goals:**
  - Verify whether this architectural change was previously evaluated and rejected.
  - Understand the maintainers' technical philosophy and architectural constraints before writing code.
- **Frustrations:**
  - Standard GitHub search returns hundreds of issues mentioning the library name, mostly consisting of bug reports and automated dependency bumps.
  - He cannot tell which discussion thread contains the authoritative consensus.
- **How Primordial Helps:** Aarav runs the Primordial CLI on the relevant historical PR URL. Within 30 seconds, he receives a structured MADR showing that the external library was evaluated and rejected due to license incompatibilities and bundle size constraints, saving him 20 hours of futile coding.

### Persona 2: Dr. Elena Rostova — Core Repository Maintainer
- **Role & Background:** Principal Software Architect and core maintainer of a widely used distributed systems library on GitHub (25,000+ stars).
- **Context:** Elena oversees 50+ pull requests weekly. Every few weeks, a contributor opens a PR proposing to replace the project's internal binary protocol parser with a JSON-based schema.
- **Goals:**
  - Quickly produce authoritative, verifiable documentation explaining why binary protocols were chosen over JSON.
  - Establish a version-controlled ADR directory (`docs/adr/`) without spending weekends writing Markdown records from scratch.
- **Frustrations:**
  - Writing ADRs manually is tedious and consistently deprioritized during active development.
  - When closing redundant PRs, she spends 15 minutes searching for the specific comment where the performance trade-offs were originally benchmarked.
- **How Primordial Helps:** Elena feeds the original PR URL into Primordial, generates a verified MADR document with direct permalinks to her team's benchmark comments, and commits `0014-binary-protocol-parser.md` into the repository.

### Persona 3: Marcus Vance — Senior Software Engineer Joining an Existing Project
- **Role & Background:** Senior Backend Engineer joining a company whose core product is built on top of an open-source payment orchestration framework.
- **Context:** Marcus is tasked with refactoring the database connection pool. He discovers an unusual retry pattern with custom backoff logic that seems counter-intuitive.
- **Goals:**
  - Discover *why* the original team implemented custom retry loops rather than using the database driver's native retry mechanism.
  - Determine if the underlying constraints still apply or if the code can be modernized.
- **Frustrations:**
  - The commit message simply reads: *"Fix pool timeout under load (#1402)"*.
  - PR #1402 contains 78 comments between three engineers debating deadlocks, cloud proxy timeouts, and driver bugs.
- **How Primordial Helps:** Marcus inputs PR #1402 into Primordial. Primordial extracts the explicit rationale: the cloud database proxy drops silent connections after 60 seconds without emitting TCP RST packets. Marcus now has complete context and knows exactly what constraints his refactored solution must respect.

---

## 4. Phased Development & Interaction Strategy

To ensure practical execution for a three-member student team during Hacktoberfest, Primordial follows a **strict three-phase development progression**. The React dashboard is **not** a prerequisite for the initial working MVP.

```
+----------------------------------------------------------------------------------------------------+
|                                    PRIMORDIAL PHASED ROADMAP                                       |
+----------------------------------------------------------------------------------------------------+

  [ PHASE 1: CORE BACKEND & CLI (MVP Target) ]
  * GitHub URL validation & REST API ingestion (Issues, PRs, Reviews)
  * Discussion preprocessing & token budgeting
  * Decision classification & structured extraction (Ollama candidate: Qwen 2.5 7B)
  * Level 1 technical evidence verification (Comment ID & permalink validation)
  * MADR 3.0.0 Markdown generation
  * Direct CLI output: stdout, JSON file, and Markdown file

                   |
                   v
  [ PHASE 2: BACKEND API SERVICE ]
  * FastAPI application exposing the working pipeline
  * Synchronous endpoint: POST /api/v1/extract
  * SQLite persistence (WAL mode) with Full-Text Search (FTS5)
  * Retrieval endpoints: GET /api/v1/decisions, GET /api/v1/decisions/{id}
  * API health check & rate-limit error reporting

                   |
                   v
  [ PHASE 3: REACT WEB DASHBOARD (Later Phase) ]
  * React + Vite + Tailwind CSS single-page interface
  * Clean URL submission bar with pre-set sample pills
  * Indeterminate loading spinner for synchronous extraction
  * Dual-pane results viewer: formatted MADR preview + interactive evidence cards
  * One-click "Copy Markdown" and "Download .md" buttons
```

---

## 5. Complete User Journey (CLI & Web)

### Text-Based User Journey Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                      PRIMORDIAL USER JOURNEY                                       |
+----------------------------------------------------------------------------------------------------+

  [ 1. INPUT STAGE ]
       |
       +---> User enters GitHub URL:
       |     * CLI: `primordial extract https://github.com/nodejs/node/pull/41749 --format markdown`
       |     * Web: Pastes URL into search bar and clicks "Recover Decision"
       |
       v
  [ 2. VALIDATION & GITHUB INGESTION ]
       |
       +---> System validates URL syntax (owner, repo, type: issue/pull, number)
       |     * If invalid: immediate error returned
       |
       +---> Fetches discussion via GitHub REST API v3:
       |     * Issue/PR title and description
       |     * Conversation comments (paginated)
       |     * Inline code review comments & review summaries (PRs only)
       |     * Checks rate limits via response headers
       |
       v
  [ 3. PREPROCESSING & AI EXTRACTION (Synchronous) ]
       |
       +---> Normalizes comments; removes bot spam (e.g., dependabot[bot]); preserves code fences
       +---> Enforces context budgeting using chronological chunking if thread exceeds budget
       +---> Runs Stage 1: Decision Classification (Candidate: Qwen 2.5 7B via Ollama)
       |     * If is_decision == False: returns early with non-decision summary
       +---> Runs Stage 2: Structured Rationale Extraction
       |     * Extracts context, chosen option, considered options, trade-offs, consequences
       +---> Runs Level 1 Technical Evidence Verification:
       |     * Validates that cited comment IDs exist in the fetched discussion
       |     * Flags unverified or missing citations
       +---> Compiles MADR 3.0.0 Markdown document
       |
       v
  [ 4. OUTPUT & CONSUMPTION ]
       |
       +---> CLI Output:
       |     * Displays formatted Markdown or JSON in terminal
       |     * Saves to `0001-adopt-undici-for-built-in-fetch-api.md`
       |
       +---> Web Dashboard Output (Phase 3):
       |     * Replaces loading indicator with Dual-Pane Viewer
       |     * Left Pane: Rendered MADR 3.0.0 Markdown
       |     * Right Pane: Interactive Evidence Drawer with permalinks to GitHub comments
```

---

## 6. Step-by-Step Interaction Specifications

### CLI Interaction Flow (Phase 1 — MVP Core)

The CLI is the primary delivery interface for Phase 1. It operates directly from the terminal without requiring a web browser or Node.js runtime.

```bash
# Basic usage: Extract and print MADR to stdout
primordial extract https://github.com/nodejs/node/pull/41749

# Save directly to a Markdown ADR file
primordial extract https://github.com/nodejs/node/pull/41749 --output docs/adr/0001-fetch.md

# Output canonical JSON for pipeline debugging or scripting
primordial extract https://github.com/nodejs/node/pull/41749 --format json --output decision.json

# Process with a local offline fixture (for reliable demo without internet)
primordial extract https://github.com/nodejs/node/pull/41749 --fixture tests/fixtures/nodejs_fetch_pr.json
```

**Terminal User Experience:**
1. User invokes `primordial extract <url>`.
2. A lightweight terminal spinner or progress line appears:
   ```text
   [*] Validating URL: https://github.com/nodejs/node/pull/41749
   [*] Fetching PR details and comments from GitHub API... (112 comments ingested)
   [*] Preprocessing discussion thread... (22 substantive comments retained)
   [*] Analyzing discussion with local AI model (qwen2.5:7b-instruct)...
   [*] Technical decision detected. Extracting rationale and trade-offs...
   [*] Verifying evidence citations against source comment IDs... (3/3 verified)
   [*] Generating MADR 3.0.0 record...
   [+] Decision successfully recovered: "Adopt Undici as Foundation for Built-in Fetch API"
   [+] Output written to: docs/adr/0001-fetch.md
   ```

---

### Web Dashboard Interaction Flow (Phase 3 — Later Phase)

1. **Input Submission:**
   - The user opens the web application (`http://localhost:5173`).
   - The user pastes a public GitHub Issue or PR URL into the search bar.
   - Client-side regex checks URL syntax immediately. If invalid, the submission button remains disabled and an inline hint is displayed.
2. **Synchronous Execution & Loading State:**
   - The user clicks **"Recover Decision"**.
   - Because the backend extraction is synchronous for the MVP (`POST /api/v1/extract`), the UI displays an **indeterminate loading spinner** with helpful messaging:
     *"Analyzing GitHub discussion thread using local AI model. This typically takes 20–45 seconds depending on discussion length..."*
   - Note: The initial MVP does **not** claim real-time multi-stage SSE progress streaming, as the backend executes synchronously in a single HTTP request cycle.
3. **Results Display:**
   - On HTTP 200 response, the loading spinner dismisses and the dual-pane results view renders:
     - **Left Pane:** Formatted MADR 3.0.0 Markdown preview with syntax highlighting.
     - **Right Pane:** Evidence Drawer containing cards for each cited comment (author avatar, timestamp, claim supported, verbatim quote, and direct GitHub link).
4. **Export Actions:**
   - "Copy Markdown" copies raw MADR text to clipboard.
   - "Download .md" downloads `{number}-{slug}.md`.

---

## 7. Inputs and Outputs at Every Stage

```
+----------------------------------------------------------------------------------------------------+
|                                  INPUTS AND OUTPUTS BY STAGE                                       |
+--------------------------+---------------------------------+---------------------------------------+
| Stage                    | Input Received                  | Output Produced                       |
+--------------------------+---------------------------------+---------------------------------------+
| 1. Input Parsing         | Raw URL string                  | `GitHubTarget` (owner, repo, type, id)|
| 2. GitHub Fetch          | `GitHubTarget`, `GITHUB_TOKEN`  | Raw JSON payloads (PR, comments, revs)|
| 3. Normalization         | Heterogeneous GitHub JSON       | `CanonicalDiscussionThread`           |
| 4. Preprocessing         | Canonical thread                | `CleanedDiscussionThread` (no bots)   |
| 5. Context Budgeting     | Cleaned thread                  | Chronological prompt transcript chunk |
| 6. Decision Detection    | Transcript chunk                | `DecisionClassificationResult`        |
| 7. Rationale Extraction  | Transcript chunk + metadata     | Raw JSON structured extraction        |
| 8. Schema Validation     | Raw JSON string                 | `ExtractedDecisionSchema` (Pydantic)  |
| 9. Evidence Verification | Extracted schema + raw comments | `VerifiedDecisionPayload` (Level 1)   |
| 10. MADR Compilation     | Verified payload                | Formatted MADR 3.0.0 Markdown string  |
+--------------------------+---------------------------------+---------------------------------------+
```

---

## 8. Main User-Facing Features & MoSCoW Mapping

```
+----------------------------------------------------------------------------------------------------+
|                                    MOSCOW FEATURE MATRIX                                           |
+----------------+-------------------------------------+---------------------------------------------+
| Priority Level | Feature Name                        | Implementation Phase & Description          |
+----------------+-------------------------------------+---------------------------------------------+
| MUST HAVE      | GitHub URL Parser & Ingestion       | Phase 1: Ingests public issues/PRs via REST |
| (MVP Core)     | Multi-Resource Comment Collector    | Phase 1: Issues, PR comments, inline reviews|
|                | Conversational Preprocessor         | Phase 1: Strips bots, retains code blocks   |
|                | Decision Classifier Gate            | Phase 1: Distinguishes decisions from bugs  |
|                | Structured Rationale Extractor      | Phase 1: Extracts chosen/rejected options   |
|                | Level 1 Technical Evidence Verifier | Phase 1: Matches cited IDs to real comments |
|                | MADR 3.0.0 Markdown Generator       | Phase 1: Produces standard MADR documents   |
|                | Primordial CLI Interface            | Phase 1: Terminal commands for extraction   |
|                | Local Open-Weight Model Execution   | Phase 1: Runs via Ollama (Qwen 2.5 7B)      |
+----------------+-------------------------------------+---------------------------------------------+
| SHOULD HAVE    | FastAPI Backend Wrapper             | Phase 2: Exposes POST /api/v1/extract       |
| (High Value)   | Local SQLite Storage with FTS5      | Phase 2: Persists decisions & enables search|
|                | React Web Dashboard                 | Phase 3: Single-page UI with dual-pane view |
|                | Evidence Drawer with Permalinks     | Phase 3: Interactive comment citations     |
+----------------+-------------------------------------+---------------------------------------------+
| COULD HAVE     | Batch PR Ingestion Script           | Phase 3: Process 5 PRs sequentially via CLI |
| (If Time)      | Offline Fixture Demonstration Mode  | Phase 2: Ingest from local mock JSON        |
|                | Markdown File Export / Copy         | Phase 3: One-click clipboard and file save  |
+----------------+-------------------------------------+---------------------------------------------+
| FUTURE SCOPE   | Asynchronous Job Queue & Polling    | Post-Hackathon: Celery/Redis background jobs|
| (Beyond MVP)   | GitHub Discussions GraphQL Support  | Post-Hackathon: Query Discussions API       |
|                | Full-Repository Crawling            | Post-Hackathon: Index 1,000+ historical PRs |
|                | Semantic Vector Embeddings (RAG)    | Post-Hackathon: Dense retrieval with BGE    |
|                | GitHub Action CI/CD Bot             | Post-Hackathon: Auto-draft ADR on PR merge  |
+----------------+-------------------------------------+---------------------------------------------+
```

---

## 9. Error, Edge, and Empty States

| Error State | Trigger Cause | User Presentation (CLI & Web) | Recommended User Recovery Action |
|---|---|---|---|
| **Invalid URL Syntax** | User enters non-GitHub string or malformed URL. | *"Error: Invalid GitHub URL. Expected format: `https://github.com/:owner/:repo/(issues\|pull)/:number`"* | Check URL syntax and re-submit. |
| **Repository Not Found (404)** | Repository is private, deleted, or mistyped. | *"Error (HTTP 404): Repository or discussion thread not found. Please verify that the repository is public."* | Check repository visibility and spelling. |
| **GitHub Rate Limit Exceeded (403/429)** | 60 unauthenticated requests/hr exhausted. | *"Error (HTTP 403): GitHub API rate limit reached. Reset at [Timestamp]. Configure GITHUB_TOKEN in backend .env to increase limit to 5,000 req/hr."* | Configure `GITHUB_TOKEN` in `.env` or wait for reset. |
| **No Decision Detected (Non-Decision)** | Issue is purely a bug fix, typo patch, or chore. | *"Informational: Primordial analyzed 18 comments. While technical discussion occurred, no architectural decision or alternative evaluation was identified."* | Normal behavior; no false ADR is generated. Summary displayed. |
| **Insufficient Evidence** | Discussion proposes a change but maintainers never reached consensus. | Generates an ADR skeleton with `status: "proposed"` or `"insufficient_evidence"`, explicitly stating: *"Public discussion ended without recorded maintainer consensus."* | Maintainers can complete the record manually. |
| **Ollama Service Offline (503)** | Local Ollama daemon is not running on `:11434`. | *"Error: Could not connect to local AI service at http://localhost:11434. Ensure Ollama is running (`ollama serve`)."* | Start Ollama service in terminal. |
| **Discussion Truncated** | Discussion exceeds model token budget. | Warning banner: *"Notice: Discussion exceeded token budget. Processed 45 of 68 comments using chronological chunking."* | Review incomplete context indicator. |

---

## 10. Detailed Illustrative Walkthrough: Node.js Built-in Fetch PR

> **Note on Example Authenticity:**  
> The discussion topic (Node.js PR #41749 "lib: add fetch", Issue #19393, and the adoption of `undici`) is an authentic, publicly documented architectural decision. However, specific comment IDs (`1034981`, `1035120`, `1036044`) used below are **illustrative test fixtures** designed to demonstrate the canonical JSON schema and MADR rendering without depending on live network data during development testing.

### Step 1: User Submits Command
```bash
primordial extract https://github.com/nodejs/node/pull/41749 --output docs/adr/0001-fetch.md
```

### Step 2: System Processing
1. Target resolved: `owner="nodejs"`, `repo="node"`, `type="pull"`, `number=41749`.
2. Ingestion fetches PR description, 112 conversation comments, and inline review comments.
3. Preprocessor strips bot comments (`codecov[bot]`, CI status notices), isolating 22 substantive technical comments.
4. Model evaluates the discussion, classifying it as an architectural decision (`is_decision: true`).
5. Model extracts structured options: `undici` engine (chosen), `node-fetch` wrapper (rejected), C++ scratch client (rejected), status quo (rejected).
6. Level 1 Evidence Verifier checks cited comment IDs against the ingested payload.
7. Compiler formats the MADR document.

### Step 3: Resulting MADR 3.0.0 Output

```markdown
# 0001 - Adopt Undici as the Foundation for Built-in Fetch API

* **Status:** accepted
* **Date:** 2022-02-03
* **Deciders:** Node.js Technical Steering Committee (TSC) & Contributors
* **Source Discussion:** [nodejs/node PR #41749](https://github.com/nodejs/node/pull/41749)

## Context and Problem Statement

For years, Node.js lacked a built-in HTTP client compliant with web standards. Developers relied on third-party npm packages (`axios`, `node-fetch`), causing ecosystem fragmentation. How should Node.js provide an ergonomic, spec-compliant global `fetch()`?

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

## 11. Additional Real-World Use Cases

### Use Case A: Pre-PR Feasibility & Rejection Audit
- **Scenario:** A contributor wants to introduce a new compression algorithm (e.g., Zstandard) into an open-source database engine.
- **Workflow:** The contributor runs `primordial extract <url>` on a closed PR from two years prior where Zstandard was debated.
- **Outcome:** The extracted ADR reveals that while compression ratios were superior, memory allocation spikes on low-RAM containers caused fatal OOM errors. The contributor designs their new proposal specifically around a memory-bounded streaming buffer, addressing the maintainers' prior objections upfront.

### Use Case B: Automated Release Milestone Decision Capture
- **Scenario:** An open-source project maintainer prepares a major v2.0 release containing 45 merged pull requests.
- **Workflow:** The maintainer runs Primordial across the milestone PRs via a CLI batch script.
- **Outcome:** Primordial filters out 38 routine bug fixes and extracts 7 core architectural decisions (e.g., migration to TypeScript strict mode, drop of Node 16, switch to ES Modules), compiling an immediate `docs/adr/` collection for release documentation.

### Use Case C: Architectural Archeology During Code Refactoring
- **Scenario:** An engineer joining a project discovers a complex locking mechanism around a cache dictionary that degrades concurrency.
- **Workflow:** The engineer traces the git commit to PR #312 and inputs PR #312 into Primordial.
- **Outcome:** Primordial recovers the ADR explaining that the locks were a defensive workaround for a race condition in an old runtime version. Because the team has upgraded to a modern runtime where that bug is patched, the engineer can safely remove the lock with high confidence.

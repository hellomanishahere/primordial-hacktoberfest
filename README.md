# Primordial

### Open Source Decision Intelligence and Knowledge Recovery

Primordial is an AI-powered engineering knowledge recovery platform
designed to extract architectural decisions, technical trade-offs, and
rejected alternatives from public GitHub discussions.

It helps developers understand not only *what* decisions were made in an
open-source project, but also *why* they were made, what alternatives
were considered, and where the original evidence can be found.

------------------------------------------------------------------------

## Problem Statement

**PS06 --- Open Source Decision Intelligence and Knowledge Recovery**

Important engineering decisions are often buried in lengthy GitHub
issues, pull requests, and review discussions. As projects evolve, this
context becomes difficult to retrieve, increasing the risk of repeating
rejected approaches or introducing changes that conflict with
established architectural decisions.

Primordial addresses this problem by recovering structured,
evidence-backed decision records from developer discussions.

## Key Objectives

-   Extract architectural and technical decisions from GitHub issues and
    pull requests.
-   Identify accepted approaches and rejected alternatives.
-   Recover the technical reasoning behind design choices.
-   Generate structured Architectural Decision Records (ADRs).
-   Preserve references to original discussion comments for
    verification.
-   Associate recovered decisions with relevant source code.

## Development Roadmap

Primordial follows a phased development approach.

  -----------------------------------------------------------------------
  Phase                   Scope                   Status
  ----------------------- ----------------------- -----------------------
  Phase 1                 Core extraction         MVP
                          pipeline and CLI        

  Phase 2                 FastAPI service, SQLite Planned
                          persistence and         
                          full-text search        

  Phase 3                 React dashboard and     Future
                          interactive evidence    
                          viewer                  
  -----------------------------------------------------------------------

### Phase 1 --- Core CLI

The initial implementation focuses on:

1.  GitHub issue and pull request ingestion.
2.  Discussion preprocessing and noise reduction.
3.  Decision detection and classification.
4.  Extraction of accepted decisions and rejected alternatives.
5.  Technical evidence verification.
6.  MADR-compatible Markdown generation.
7.  Command-line execution.

### Phase 2 --- Backend API

The next phase will introduce:

-   FastAPI service.
-   Synchronous decision extraction endpoint.
-   SQLite persistence using Write-Ahead Logging (WAL).
-   SQLite FTS5 full-text search.
-   Decision retrieval endpoints.

### Phase 3 --- Web Dashboard

The planned frontend will provide:

-   Repository and discussion submission.
-   Structured decision visualization.
-   Architectural Decision Record previews.
-   Interactive evidence references.
-   Decision browsing and search.

------------------------------------------------------------------------

## System Architecture

Primordial uses a modular Python backend with locally executed
open-weight language models.

``` text
             GitHub Issue / Pull Request
                       |
                       v
              GitHub Data Ingestion
                       |
                       v
             Discussion Preprocessing
                       |
                       v
              Context Construction
                       |
                       v
              Decision Classification
                       |
                       v
             Structured Extraction
                       |
                       v
              Evidence Verification
                       |
                       v
                MADR Compiler
                       |
                       v
             Decision Record Output
```

## Technology Stack

  Component                 Technology
  ------------------------- ----------------------------
  Backend                   Python 3.11+
  AI Inference              Ollama
  Primary candidate model   Qwen 2.5 7B (`qwen2.5:7b`)
  Data validation           Pydantic
  GitHub integration        GitHub REST API
  Database (Phase 2)        SQLite with WAL
  Search (Phase 2)          SQLite FTS5
  API (Phase 2)             FastAPI
  Frontend (Phase 3)        React

The architecture prioritizes local inference and avoids sending
discussion content to paid, closed-source cloud AI APIs.

The model listed above is the documented candidate configuration; actual
model availability and execution depend on the local Ollama setup.

------------------------------------------------------------------------

## Getting Started

### Prerequisites

For the Phase 1 CLI implementation:

-   Python 3.11 or newer
-   Git
-   [Ollama](https://ollama.com/)
-   A compatible local model downloaded through Ollama
-   Internet access for public GitHub repository ingestion

### 1. Clone the repository

``` bash
git clone https://github.com/YOUR_USERNAME/primordial-hacktoberfest.git
cd primordial-hacktoberfest
```

### 2. Set up the Python environment

``` bash
cd backend
python -m venv .venv
```

Activate the environment:

**macOS / Linux**

``` bash
source .venv/bin/activate
```

**Windows**

``` powershell
.venv\Scripts\activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure Ollama

Install and start Ollama, then download the configured model:

``` bash
ollama pull qwen2.5:7b
```

Ensure the Ollama service is running before executing the extraction
pipeline.

### 5. Configure environment variables

Create a `.env` file inside `backend/` when required by the
implementation.

Example:

``` env
GITHUB_TOKEN=your_github_token
OLLAMA_BASE_URL=http://localhost:11434
AI_MODEL_PRIMARY=qwen2.5:7b
AI_MODEL_FALLBACK=llama3.1:8b
```

A GitHub token is optional for public repository access, but can
increase API rate limits. Never commit your `.env` file or expose
credentials.

### 6. Run the CLI

From the `backend/` directory:

``` bash
python -m app.cli extract https://github.com/OWNER/REPOSITORY/pull/NUMBER
```

The CLI is the primary interface for Phase 1. Exact options and output
formats are documented alongside the implementation.

> **Development status:** Setup instructions describe the intended Phase
> 1 execution path. Commands and configuration should be considered
> operational only once the corresponding implementation is available.

------------------------------------------------------------------------

## Decision Records

Primordial structures recovered decisions into a consistent,
machine-readable format.

A decision record is designed to include:

-   Decision title and status.
-   Context and problem statement.
-   Chosen approach.
-   Considered and rejected alternatives.
-   Technical reasoning and consequences.
-   Related source files.
-   Original discussion references.
-   Evidence verification information.
-   Confidence score.

Records can also be compiled into Markdown Architectural Decision
Records.

**Evidence integrity:** Primordial distinguishes technical reference
validation from semantic review. A valid comment permalink does not
automatically prove that an extracted claim is semantically correct;
human verification remains important.

------------------------------------------------------------------------

## Testing and Continuous Integration

The repository uses GitHub Actions for automated validation.

CI is configured to run on pull requests targeting `main` and pushes to
`main`.

The workflow is intended to:

-   Install Python dependencies.
-   Validate Python syntax.
-   Execute automated tests.
-   Validate the CLI entry point.

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the
workflow configuration.

------------------------------------------------------------------------

## Repository Structure

``` text
primordial-hacktoberfest/
│
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── github/
│   │   ├── domain/
│   │   ├── pipeline/
│   │   ├── storage/
│   │   ├── cli.py
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/                 # Phase 3
├── tests/
├── examples/
│
├── HACKATHON.md
├── LICENSE
└── README.md
```

The directory structure represents the planned modular architecture.
Components will be introduced incrementally as development progresses.

------------------------------------------------------------------------

## Team

**Team Primordial**

  Member            Role
  ----------------- -------------
  Shaurya Negi      Development
  Prince Chhikara   Development
  Manisha Jain      Development

**Event:** Hacktoberfest 2026 --- Hack Day Sonipat\
**Institution:** Newton School of Technology, Rishihood University

------------------------------------------------------------------------

## Contribution Guidelines

Primordial follows a pull-request-driven development workflow.

1.  Create a feature branch from `main`.
2.  Implement and test your changes.
3.  Commit changes to your feature branch.
4.  Open a pull request using `.github/pull_request_template.md`.
5.  Document product models and AI coding assistants used.
6.  Ensure all configured CI checks pass.
7.  Merge the pull request after successful validation.

Direct commits to `main` are not permitted after the initial repository
commit.

------------------------------------------------------------------------

## License

This project is licensed under the [MIT License](LICENSE).

# Primordial: Corrected Technical Documentation Suite

**Project Name:** Primordial  
**Repository:** `primordial-hacktoberfest`  
**Team Name:** Primordial  
**Team Members:** Shaurya Negi, Prince Chhikara, Manisha Jain  
**Hackathon:** Hacktoberfest 2026 – Hack Day Sonipat  
**Institution:** Newton School of Technology, Rishihood University  
**Problem Statement:** Problem Statement 06 — Open Source Decision Intelligence and Knowledge Recovery  
**Documentation Version:** 2.0.0 (Implementation-Ready Revision)

---

## Overview

This directory contains the **corrected, implementation-ready technical documentation suite** for **Primordial**, an AI-powered Decision Intelligence and Knowledge Recovery platform.

This revision resolves the major architectural inconsistencies, unifies the canonical JSON and Pydantic schemas, establishes a realistic three-phase development progression (CLI-first MVP), corrects evidence validation claims, refines context budgeting, standardizes repository structure, and aligns all technical specifications for a three-member student engineering team.

---

## Document Index and Reading Order

```
+-----------------------------------------------------------------------------------------------------------------+
|                                    DOCUMENTATION SUITE INDEX & READING ORDER                                    |
+----+---------------------------------------------------------------+--------------------------------------------+
| #  | Document Filename                                             | Purpose & Target Audience                  |
+----+---------------------------------------------------------------+--------------------------------------------+
| 01 | `01-user-workflow-and-use-cases.md`                           | User experience, personas, step-by-step    |
|    |                                                               | user journeys (CLI & Web), error/empty     |
|    |                                                               | states, and illustrative walkthroughs.     |
+----+---------------------------------------------------------------+--------------------------------------------+
| 02 | `02-problem-statement-and-research.md`                        | Verified academic research foundation,     |
|    |                                                               | qualified competitor analyses, real-world  |
|    |                                                               | case studies, and MVP scope boundaries.    |
+----+---------------------------------------------------------------+--------------------------------------------+
| 03 | `03-solution-and-feature-specification.md`                    | Product vision, MoSCoW feature breakdown,  |
|    |                                                               | canonical Pydantic schema, functional and  |
|    |                                                               | non-functional requirements, and Gherkin.  |
+----+---------------------------------------------------------------+--------------------------------------------+
| 04 | `04-technical-workflow-and-data-pipeline.md`                  | Internal 12-stage data pipeline, GitHub    |
|    |                                                               | API collection, chronological context      |
|    |                                                               | budgeting, anti-hallucination safeguards.  |
+----+---------------------------------------------------------------+--------------------------------------------+
| 05 | `05-system-architecture-and-implementation-design.md`         | System architecture, Mermaid diagrams,     |
|    |                                                               | 3-phase development progression, backend   |
|    |                                                               | modules, SQLite WAL schema, candidate AI   |
|    |                                                               | model analysis, and decision registry.     |
+----+---------------------------------------------------------------+--------------------------------------------+
| 06 | `06-complete-technical-research-implementation-and-testing.md`| Master engineering reference: API contract,|
|    |                                                               | production AI prompts, planned test suite, |
|    |                                                               | evaluation metrics, milestones, work       |
|    |                                                               | division, and live judging demo script.    |
+----+---------------------------------------------------------------+--------------------------------------------+
```

---

## Recommended Reading Paths

### Path A: For Developers Implementing the Core Pipeline (Phase 1 CLI)
1. Read `05-system-architecture-and-implementation-design.md` (Section 4) for standardized directory structure and module interfaces.
2. Read `04-technical-workflow-and-data-pipeline.md` (Section 2) for the 12 sequential pipeline stages.
3. Read `06-complete-technical-research-implementation-and-testing.md` (Sections 5, 6, 7, and 8) for the exact Pydantic models, production AI prompts, and Pytest test specifications.

### Path B: For API & Frontend Developers (Phases 2 & 3)
1. Read `01-user-workflow-and-use-cases.md` to understand user interactions, loading indicators, and export actions.
2. Read `03-solution-and-feature-specification.md` (Section 5) for the canonical data schema.
3. Read `05-system-architecture-and-implementation-design.md` (Sections 5 & 6) and `06-complete-technical-research-implementation-and-testing.md` (Section 5) for the synchronous API contract.

### Path C: For Hackathon Judges & Technical Reviewers
1. Read `02-problem-statement-and-research.md` for problem justification, academic grounding, and qualified competitor teardowns.
2. Read `03-solution-and-feature-specification.md` for the MoSCoW scope and feature criteria.
3. Read Section 13 of `06-complete-technical-research-implementation-and-testing.md` for the 5-minute live demonstration script.

---

## Key Revisions and Corrections in this Suite

1. **Phased Development Alignment:** Clearly distinguishes Phase 1 (Core Backend & CLI as Must Have MVP), Phase 2 (FastAPI Service as Should Have), and Phase 3 (React Dashboard as Later Phase).
2. **Synchronous Execution Modeling:** Replaced unsupported real-time streaming claims with a reliable synchronous API (`POST /api/v1/extract`) with an indeterminate loading spinner. Asynchronous job queues are documented as pending post-hackathon enhancements.
3. **Canonical Data Schema:** Unified all field names (`consequences.positive`, `consequences.negative`, `considered_options`, `chosen_option` nullable, `evidence_ids`, `context_metadata`) across every document.
4. **Two-Level Evidence Verification:** Explicitly separated Level 1 Technical Verification (automated ID, author, and permalink existence check) from Level 2 Semantic Verification (human-assisted claim review). Removed all "zero hallucinations" and "100% semantic correctness" claims.
5. **Context Window Management:** Replaced arbitrary comment truncation with principled chronological chunking with overlap and explicit `was_truncated` reporting.
6. **Token Security:** Standardized on backend environment variable `GITHUB_TOKEN` from `.env`. Eliminated client-side token headers.
7. **Empirical Model Claims:** Standardized on candidate model `qwen2.5:7b` via Ollama. Replaced unverified throughput and accuracy claims with an empirical evaluation plan, marking hardware benchmarks as PENDING until tested. Clarified that `confidence_score` is an internal model heuristic, not a calibrated probability.
8. **Testing Integrity:** Clearly distinguished planned test specifications from implemented and executed tests.

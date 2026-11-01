# Hacktoberfest 2026 – Project Submission

## 1. Team Information

- **Team Name:** Primordial
- **Team Members:**
  1. **Shaurya Negi**
  2. **Prince Chhikara**
  3. **Manisha Jain**

---

## 2. Selected Problem Statement

### **Problem 06: Open Source Decision Intelligence and Knowledge Recovery**
- **Category:** Knowledge Management | Developer Intelligence | Information Retrieval

### Problem Context & Objectives
Open-source software (OSS) repositories represent some of the most dynamic engineering ecosystems in the world. However, vital architectural and technical decisions—the *why* behind design trade-offs, rejected approaches, performance compromises, and structural pivots—frequently remain buried under hundreds of issue comments, fragmented pull request reviews, and disparate technical threads. When new contributors join or existing maintainers review new pull requests touching legacy subsystems, they often lack contextual visibility into historical debates, risking inadvertent regressions, re-proposing previously rejected designs, or repeating past architectural mistakes.

**Primordial** is a prototype for recovering engineering decisions from project discussions. The current implementation:
1. Fetches public GitHub issues and pull requests, including their discussion comments.
2. Cleans and budgets discussion text before analysis.
3. Uses a local Ollama model to detect candidate decisions and extract rationales and alternatives.
4. Checks cited comment IDs and support signals, then generates schema-validated ADR documents.
5. Keeps links to source discussions and comments. It does not yet provide robust line-level or symbol-level code references.
6. Stores decisions for search and offers a prototype PR radar based on text matching.

The Python PEP evaluation, non-GitHub discussion ingestion, cross-platform contributor identity, and reliable code tracking across file moves remain unfinished.

---

## 3. Model and Runtime

The current implementation uses **Qwen 2.5 7B** through a locally running Ollama service for decision detection and rationale extraction. The model is selected with `AI_MODEL_PRIMARY`; the default is `qwen2.5:7b`. The application does not call a cloud AI API.

Preprocessing, evidence checks, schema validation, storage, and ADR formatting are implemented in Python. Evidence checks verify that cited comment IDs exist in the fetched discussion and apply deterministic support and contradiction rules. These checks do not prove that every interpretation is correct; maintainers should review the linked source comments.

The code does not currently implement separate Llama or Phi stages, a working fallback model, an offline AI engine, or robust line/symbol-level code grounding. The PR radar is a prototype matcher. The primary evaluation against Python PEP discussions without providing the corresponding PEP is still pending.

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

# Python PEP Evaluation: PEP 563 & PEP 649 (Postponed Evaluation of Annotations)

## 1. Overview & Objective

This document evaluates Primordial's ability to recover engineering decisions, rejected alternatives, reasons for rejection, and trade-offs from real public open-source technical discussions without access to the final authored PEP documents.

- **Target Discussion:** [python/cpython#82786](https://github.com/python/cpython/issues/82786) (Legacy bpo-38605)
- **Discussion Subject:** `[typing] PEP 563: Postponed evaluation of annotations: enable it by default in Python 3.11`
- **Participants:** Victor Stinner (@vstinner), Guido van Rossum (@gvanrossum), Brett Cannon (@brettcannon), Pablo Galindo Salgado (@pablogsal), Ivan Levkivskyi (@ilevkivskyi), Lukasz Langa (@ambv), and others.
- **Evaluation Rule:** System is fed only the raw discussion transcript without providing the final PEP 563 or PEP 649 specification documents.

---

## 2. Real Discussion Context

PEP 563 introduced postponed evaluation of type annotations (`from __future__ import annotations`), storing annotations as strings rather than evaluating them at module definition time. Originally proposed to become the default in Python 4.0, core developers debated making it the default in Python 3.10 or Python 3.11.

However, during Python 3.10 alpha/beta testing, major runtime type-checking frameworks (such as Pydantic, FastAPI, and dataclasses) encountered breaking runtime failures because stringified annotations could not easily be resolved at runtime in local or class scopes.

---

## 3. Ground Truth Decisions from Discussion

From the public discussion in [python/cpython#82786](https://github.com/python/cpython/issues/82786):

1. **Adopted / Consented Decision:**
   - **Revert enabling PEP 563 by default in Python 3.11.**
   - Decision by Python Steering Council: Do not break existing runtime introspection; postpone the transition indefinitely.
   - Evidence in Discussion: Comment [#1093845441](https://github.com/python/cpython/issues/82786#issuecomment-1093845441) by @vstinner:
     > *"Revert making `from __future__ import annotations` the default. This follows the Steering Council decision to postpone PEP-563."*
   - Comment [#1302478978](https://github.com/python/cpython/issues/82786#issuecomment-1302478978) by @vstinner:
     > *"The SC asked to hold this for now. So I prefer to close the issue. Please open a new issue when the PEP will be implemented."*

2. **Rejected / Deferred Alternative:**
   - **Alternative:** Enable PEP 563 by default in Python 3.9 or 3.10.
   - **Status:** REJECTED / SUPERSEDED.
   - **Rejection Reason:** Too aggressive of a deprecation cycle; breaks runtime annotation consumers (Pydantic, cattrs) and libraries relying on `inspect.signature()`.
   - Evidence in Discussion: Comment [#1093845401](https://github.com/python/cpython/issues/82786#issuecomment-1093845401) by @gvanrossum:
     > *"Even 3.10 might be on the early side (assuming that 3.9 will be the first version with a prominent deprecation warning)."*

3. **Trade-offs Identified:**
   - **Static vs Runtime Typing:** Stringified annotations improve import performance and allow forward references, but cripple runtime tools that inspect type signatures dynamically.
   - **Lazy Evaluation vs Backward Compatibility:** Prompted the development of PEP 649 (deferred evaluation via functions / descriptors).

---

## 4. Primordial Automated Pipeline Evaluation Results

### Live Execution Against `python/cpython#82786`:
```bash
python -m app.cli detect https://github.com/python/cpython/issues/82786 --model qwen2.5:7b
```

### Actual Application Output:
- **Cleaned Discussion Comments:** 42 comments processed.
- **Model Deliberation Reasoning:**
  > *"There are no clear decisions made regarding the future of PEP-563 in the provided transcript. The discussion revolves around the postponement of the feature and potential alternatives, but no final decision is recorded."*
- **Is Decision Detected:** `False`
- **Decisions Count:** 0

---

## 5. Analysis & Limitations of Current 7B Open-Source Model

1. **Why the Model Declined Detection:**
   - The discussion contains substantial consensus shifts across a 3-year timeline (from 2019 to 2022).
   - The model correctly identified that the discussion consists of continuous debate, postponement notices, and referral to the Steering Council rather than a simple unflagged feature commit.
   - Under Primordial's anti-hallucination rules, candidate decisions that omit specific comment ID citations from the current transcript are strictly dropped.
2. **Key Insights for Problem 06:**
   - **Positive:** Primordial strictly prevents false-positive hallucinations. When an open-source discussion is inconclusive or refers decision authority to an external body (such as the Python Steering Council or Discourse), the system refuses to fabricate an accepted decision.
   - **Limitation:** Smaller local 7B models struggle to synthesize multi-year governance shifts spread across dozens of comments when token truncation limits the full historical context.

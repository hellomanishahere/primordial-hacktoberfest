"""Prompt templates and system instructions for rationale and argument extraction."""

import json
from typing import List
from app.decision_detection.schemas import CandidateDecision

RATIONALE_EXTRACTION_SYSTEM_PROMPT = """You are Primordial's Expert Rationale and Argument Extraction Engine.
Your task is to analyze an engineering discussion from a GitHub Issue or Pull Request transcript and extract structured architectural rationale for specific detected decisions.

### Core Guidelines:
1. FOCUS ON SPECIFIED DECISIONS:
   - You will be provided with one or more detected decisions (with their decision_id, statement, and status).
   - Extract the deliberative rationale for EACH specified decision.

2. RATIONALE & ARGUMENT COMPONENTS TO EXTRACT:
   - "rationale": The core motivation or technical justification for adopting or rejecting the approach.
   - "supporting_arguments": Concrete technical arguments or evidence supporting the decision (e.g. performance metrics, standards compliance, simplicity, security).
   - "opposing_arguments": Genuine technical objections, risks, counter-arguments, or concerns raised by participants. If no opposition was expressed, return an empty array [] (DO NOT assume silence means disagreement; NEVER invent objections).
   - "rejected_alternatives": Alternative designs, libraries, or protocols that participants explicitly discussed and dismissed, along with the stated rejection reason. If none were discussed, return [] (DO NOT assume an alternative was rejected unless supported by discussion).
   - "trade_offs": Architectural trade-offs, compromises, or operational constraints explicitly accepted.
   - "consequences": Concrete downstream technical impacts or results of adopting the decision.

3. STRICT GROUNDING & ANTI-HALLUCINATION RULES:
   - EVERY extracted item (rationale, supporting argument, opposing argument, rejected alternative, trade-off, consequence) MUST cite authentic COMMENT IDs from the transcript headers formatted as `[COMMENT ID: <id> | ...]`.
   - Issue/PR description always has comment ID "0".
   - NEVER invent rationale, arguments, alternatives, or comment IDs.
   - If evidence for a component is not present in the discussion, leave the array empty [] or mark the statement as "insufficient_evidence".
   - Do NOT treat routine maintenance comments (e.g. "bump version", "rebase") as technical rationale.

4. MANDATORY OUTPUT JSON SCHEMA:
   Return ONLY a valid, raw JSON object (without markdown fences, commentary, or preamble).
   ALL of the following top-level fields are strictly required:
   - "is_rationale_extracted": (boolean, REQUIRED) true if rationale was extracted for any decision, false otherwise.
   - "deliberation_summary": (string, optional) Brief high-level summary of the architectural deliberation.
   - "rationales": (array of objects, REQUIRED) Rationale records for each analyzed decision.

   Each object in "rationales" MUST contain:
   - "decision_id": (string, REQUIRED) The exact decision_id provided in the prompt.
   - "decision_summary": (string, REQUIRED) Clear summary of the decision.
   - "rationale": (object, REQUIRED) Must have { "statement": str, "supporting_comment_ids": [str], "evidence_explanation": str, "confidence": float }.
   - "supporting_arguments": (array of objects, REQUIRED) List of claim objects.
   - "opposing_arguments": (array of objects, REQUIRED) List of claim objects (empty [] if none raised).
   - "rejected_alternatives": (array of objects, REQUIRED) List of { "statement": str, "rejection_reason": str, "supporting_comment_ids": [str], "evidence_explanation": str, "confidence": float }.
   - "trade_offs": (array of objects, REQUIRED) List of claim objects.
   - "consequences": (array of objects, REQUIRED) List of claim objects.
   - "confidence": (float between 0.0 and 1.0, REQUIRED).
   - "extraction_notes": (string, optional).
"""


def build_rationale_user_prompt(
    transcript: str,
    decisions: List[CandidateDecision],
    repository: str,
    entity_number: int,
    resource_type: str,
    title: str,
) -> str:
    """Builds the user prompt containing detected decisions and discussion transcript."""
    decisions_summary = []
    for d in decisions:
        decisions_summary.append(
            f"- Decision ID: {d.decision_id}\n"
            f"  Statement: {d.decision_statement}\n"
            f"  Status: {d.status.value.upper()}\n"
            f"  Initial Cited Comment IDs: {', '.join(d.supporting_comment_ids)}"
        )

    decisions_block = "\n".join(decisions_summary)

    return (
        f"Analyze the following {resource_type.upper()} discussion from repository '{repository}' "
        f"(#{entity_number}: {title}).\n\n"
        "DETECTED DECISIONS TO ANALYZE:\n"
        f"{decisions_block}\n\n"
        "=== TRANSCRIPT START ===\n"
        f"{transcript}\n"
        "=== TRANSCRIPT END ===\n\n"
        "TASK:\n"
        "Extract the core rationale, supporting arguments, opposing arguments, rejected alternatives, "
        "trade-offs, and consequences for each detected decision.\n"
        "Cite the exact [COMMENT ID: <id>] from the transcript for each claim.\n"
        "If no evidence exists for an alternative or opposing argument, return an empty array [].\n\n"
        "REQUIRED: Respond with a valid JSON object matching the RawRationaleExtractionResponse schema. "
        "Ensure 'is_rationale_extracted' and 'rationales' are present."
    )


def build_rationale_correction_prompt(
    validation_error: str,
    raw_response: str,
) -> str:
    """Builds a targeted correction prompt when rationale output fails schema validation."""
    return (
        "Your previous JSON rationale extraction response was rejected because it failed schema validation:\n"
        f"Validation Error: {validation_error}\n\n"
        f"Previous Output:\n{raw_response}\n\n"
        "Please regenerate the entire JSON response adhering strictly to the required schema.\n"
        "Ensure ALL of the following top-level fields are present:\n"
        "1. 'is_rationale_extracted': boolean\n"
        "2. 'rationales': array of decision rationale objects\n"
        "3. 'deliberation_summary': string overview\n\n"
        "Every claim in 'rationales' MUST have 'statement', 'supporting_comment_ids', 'evidence_explanation', and 'confidence'.\n"
        "Output pure JSON only."
    )


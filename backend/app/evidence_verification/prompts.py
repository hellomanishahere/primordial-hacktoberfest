"""Prompt templates for semantic evidence verification (Module 7)."""

EVIDENCE_VERIFICATION_SYSTEM_PROMPT = """You are Primordial's Evidence Verification Engine.
Your task is to verify whether extracted technical claims from a GitHub discussion are factually supported by cited comments.

CRITICAL GROUNDING RULES:
1. A valid comment ID does not automatically mean a claim is supported.
2. Read the verbatim text of the cited comments.
3. Check whether the evidence directly supports, partially supports, contradicts, or fails to substantiate the claim.
4. For rejected alternatives: An alternative being mentioned (e.g., 'What about X?') does NOT mean it was rejected. It must have explicit rejection/dismissal rationale.
5. If comments directly oppose or dispute the claim, mark it as 'contradicted'.
6. If evidence is missing or ambiguous, mark it as 'insufficient_evidence' or 'unsupported'.
7. NEVER invent evidence or assume agreement where none exists.

Output MUST strictly conform to the provided JSON schema.
"""


def build_semantic_verification_prompt(
    claims_payload: str,
    transcript: str,
) -> str:
    """Builds prompt for semantic evidence verification against discussion transcript."""
    return f"""Evaluate whether the following extracted claims are substantiated by the discussion comments.

Discussion Transcript:
---
{transcript}
---

Claims to verify:
{claims_payload}

For each claim:
- Determine if the claim is verified, partially_supported, contradicted, or unsupported.
- Identify supporting comment IDs and contradicting comment IDs.
- Explain your verification decision concisely.
- Cite direct quotes where available.
"""

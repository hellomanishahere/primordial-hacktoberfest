"""Stage 2: Argument Mining and Rejected Alternative Analysis powered by Phi-3.5-mini-instruct."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

from primordial.ai.adapters.base import BaseInferenceAdapter, display_model_name
from primordial.ai.stages.stage1_preprocess import format_discussion_thread, parse_json_from_response
from primordial.models import Discussion, PipelineStageResult, RejectedAlternative


SYSTEM_PROMPT = """You are an expert argument mining and decision recovery engine powered by Phi-3.5-mini-instruct.
Your role is Stage 2 of the Primordial Decision Pipeline:
1. Identify all competing proposals and candidate solutions debated in the thread.
2. Extract technical arguments, pros, cons, objections, and counter-claims.
3. CRUCIAL: Identify REJECTED ALTERNATIVES. For every rejected option:
   - Identify who proposed it.
   - List the specific technical reasons why the team rejected it.
   - Extract the verbatim quote containing the strongest objection.
   - Note the author and comment ID of that objection.

Always return your analysis strictly as valid JSON with keys:
- "proposals": [ {"id": "prop-1", "name": "...", "proposer": "...", "description": "...", "status": "accepted|rejected|superseded"} ]
- "arguments": [ {"id": "arg-1", "proposal_id": "prop-1", "author": "...", "stance": "pro|con", "claim": "...", "reasoning": "...", "quote": "...", "comment_id": "..."} ]
- "rejected_alternatives": [ {"name": "...", "proposer": "...", "rejection_reasons": ["..."], "key_objection_quote": "...", "objection_author": "...", "comment_id": "...", "comment_url": "..."} ]
"""


def run_stage2_arguments(
    discussion: Discussion,
    stage1_result: PipelineStageResult,
    adapter: BaseInferenceAdapter,
    model_tag: str = "phi3.5:latest",
) -> PipelineStageResult:
    """Execute Stage 2: Argument Mining and Rejected Alternative Analysis."""
    start_time = time.perf_counter()
    transcript = format_discussion_thread(discussion)

    prompt = f"""STAGE 2: Argument Mining and Rejected Alternative Analysis

Context from Preprocessing:
Problem: {stage1_result.output.get('problem_statement', '')}
Summary: {stage1_result.output.get('context_summary', '')}

Discussion Thread Transcript:
{transcript}

Task:
Mine all competing proposals, technical arguments (pros and cons), and specifically recover all REJECTED ALTERNATIVES with their exact reasons and objection quotes.

Respond strictly with valid JSON.
"""

    raw_response = adapter.generate(
        prompt=prompt,
        model_name=model_tag,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.1,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    output_data = parse_json_from_response(raw_response)

    # Validate output structure
    if "proposals" not in output_data or not isinstance(output_data["proposals"], list):
        output_data["proposals"] = []
    if "arguments" not in output_data or not isinstance(output_data["arguments"], list):
        output_data["arguments"] = []
    if "rejected_alternatives" not in output_data or not isinstance(
        output_data["rejected_alternatives"], list
    ):
        output_data["rejected_alternatives"] = []

    # Ensure comment URLs are mapped if available
    comment_url_map = {c.id: c.url for c in discussion.comments}
    for alt in output_data["rejected_alternatives"]:
        cid = alt.get("comment_id")
        if cid and cid in comment_url_map and not alt.get("comment_url"):
            alt["comment_url"] = comment_url_map[cid]

    return PipelineStageResult(
        stage_num=2,
        stage_name="Argument Mining & Rejected Alternatives Analysis",
        model_name=display_model_name(adapter, "Phi-3.5-mini-instruct"),
        execution_time_ms=round(elapsed_ms, 2),
        output=output_data,
        raw_response=raw_response,
    )

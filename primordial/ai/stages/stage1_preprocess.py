"""Stage 1: Discussion Preprocessing and Summarization powered by Llama 3.2-3B-Instruct."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Tuple

from primordial.ai.adapters.base import BaseInferenceAdapter
from primordial.models import Discussion, PipelineStageResult


SYSTEM_PROMPT = """You are an expert technical discussion analyzer using Llama 3.2-3B-Instruct.
Your role is Stage 1 of the Primordial Decision Pipeline: Preprocess the discussion thread, map participants, condense the timeline, and extract the core architectural problem statement.
Always return your analysis strictly as valid JSON with keys:
- "title": short title of topic
- "problem_statement": clear definition of the core architectural problem
- "context_summary": 2-3 sentence summary of why this discussion was initiated
- "participants": list of unique usernames participating
- "identified_topics": list of technical topics/tags
"""


def format_discussion_thread(discussion: Discussion) -> str:
    """Format full discussion thread into a clean, annotated transcript for the model."""
    lines = [
        f"Source: {discussion.source_type} ({discussion.source_url})",
        f"Title: {discussion.title}",
        f"Author: {discussion.author} (Created: {discussion.created_at})",
        f"Labels: {', '.join(discussion.labels) if discussion.labels else 'none'}",
        "\n--- INITIAL PROPOSAL / ISSUE DESCRIPTION ---",
        discussion.description.strip(),
        "\n--- DISCUSSION COMMENTS ---",
    ]
    for c in discussion.comments:
        lines.append(f"\n[Comment {c.id} by @{c.author} at {c.created_at}]")
        lines.append(c.body.strip())
    return "\n".join(lines)


def parse_json_from_response(raw_text: str) -> Dict[str, Any]:
    """Robustly parse JSON object from model output."""
    raw_text = raw_text.strip()
    # Try finding markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding outermost curly braces
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw_text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # Fallback structure
    return {
        "problem_statement": "Technical decision debate regarding system architecture.",
        "context_summary": raw_text[:300] if raw_text else "Discussion thread analysis.",
        "participants": [],
        "identified_topics": ["Architecture", "Configuration"],
    }


def run_stage1_preprocess(
    discussion: Discussion, adapter: BaseInferenceAdapter, model_tag: str = "llama3.2:3b"
) -> PipelineStageResult:
    """Execute Stage 1: Discussion Preprocessing & Summarization."""
    start_time = time.perf_counter()
    transcript = format_discussion_thread(discussion)

    prompt = f"""STAGE 1: Discussion Preprocessing and Summarization

Analyze the following open-source engineering discussion:

{transcript}

Extract:
1. The architectural problem statement.
2. A concise summary of the engineering context and motivations.
3. The list of active participants.
4. Key architectural topics.

Respond ONLY with valid JSON.
"""

    raw_response = adapter.generate(
        prompt=prompt,
        model_name=model_tag,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.1,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    output_data = parse_json_from_response(raw_response)

    # Ensure title and participants are populated if missing
    if "title" not in output_data or not output_data["title"]:
        output_data["title"] = discussion.title
    if "participants" not in output_data or not output_data["participants"]:
        output_data["participants"] = discussion.get_all_participants()

    return PipelineStageResult(
        stage_num=1,
        stage_name="Discussion Preprocessing & Summarization",
        model_name="Llama 3.2-3B-Instruct",
        execution_time_ms=round(elapsed_ms, 2),
        output=output_data,
        raw_response=raw_response,
    )

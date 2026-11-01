"""Decision Extraction Pipeline orchestrator for Primordial."""
from __future__ import annotations

import time
from typing import Optional

from primordial.ai.adapters import get_inference_adapter
from primordial.ai.adapters.base import BaseInferenceAdapter
from primordial.ai.stages.stage1_preprocess import run_stage1_preprocess
from primordial.ai.stages.stage2_arguments import run_stage2_arguments
from primordial.ai.stages.stage3_decision import run_stage3_decision
from primordial.models import Discussion, PipelineExecutionResult


class PrimordialDecisionPipeline:
    """Orchestrates the 3-stage open-weight AI pipeline:

    Stage 1: Llama 3.2-3B-Instruct (Discussion Preprocessing & Summarization)
    Stage 2: Phi-3.5-mini-instruct (Argument Mining & Rejected Alternatives Analysis)
    Stage 3: Qwen 2.5-Coder-7B-Instruct (Decision Synthesis & Code Grounding)
    """

    def __init__(self, adapter: Optional[BaseInferenceAdapter] = None):
        self.adapter = adapter or get_inference_adapter()

    def process_discussion(self, discussion: Discussion) -> PipelineExecutionResult:
        """Run the end-to-end multi-model pipeline on a discussion."""
        start_time = time.perf_counter()

        # Stage 1: Discussion Preprocessing & Summarization (Llama 3.2-3B)
        stage1_result = run_stage1_preprocess(
            discussion=discussion,
            adapter=self.adapter,
            model_tag="llama3.2:3b",
        )

        # Stage 2: Argument Mining & Rejected Alternatives (Phi-3.5-mini)
        stage2_result = run_stage2_arguments(
            discussion=discussion,
            stage1_result=stage1_result,
            adapter=self.adapter,
            model_tag="phi3.5:latest",
        )

        # Stage 3: Decision Synthesis & Code Grounding (Qwen 2.5-Coder-7B)
        stage3_result, decision_record = run_stage3_decision(
            discussion=discussion,
            stage1_result=stage1_result,
            stage2_result=stage2_result,
            adapter=self.adapter,
            model_tag="qwen2.5-coder:7b",
        )

        # Run Evidence Verification & MADR generation
        from primordial.adr.generator import generate_madr
        from primordial.verification.evidence import verify_evidence_quotes

        # Verify evidence quotes against discussion comments
        verified_quotes = verify_evidence_quotes(decision_record.evidence_quotes, discussion)
        decision_record.evidence_quotes = verified_quotes

        # Generate MADR markdown
        decision_record.madr_content = generate_madr(decision_record, discussion)

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return PipelineExecutionResult(
            discussion_id=discussion.id,
            stages=[stage1_result, stage2_result, stage3_result],
            final_decision=decision_record,
            total_time_ms=round(total_elapsed_ms, 2),
        )

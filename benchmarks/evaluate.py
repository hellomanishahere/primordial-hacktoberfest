"""Automated evaluation suite for Hacktoberfest 2026 Problem Statement 06."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors.dataset_loader import get_sample_discussions
from primordial.models import PullRequestDiff
from primordial.radar.pr_scanner import PRDecisionRadar
from primordial.storage.db import DecisionStorage


GROUND_TRUTH_BENCHMARKS = [
    {
        "discussion_id": "gh:astral-sh/uv/issues/1042",
        "expected_accepted": "TOML",
        "expected_rejected": ["YAML", "JSON"],
        "key_rejected_terms": ["yaml", "json"],
        "radar_test_pr": {
            "title": "Add YAML config parsing for uv",
            "changed_files": ["uv.yaml", "config.py"],
            "patch_diff": "+ import yaml\n+ yaml.safe_load()",
            "should_alert": True,
            "expected_conflict": "resurrected_rejected_alternative",
        },
    },
    {
        "discussion_id": "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219",
        "expected_accepted": "SQLite",
        "expected_rejected": ["RocksDB"],
        "key_rejected_terms": ["rocksdb"],
        "radar_test_pr": {
            "title": "Introduce RocksDB caching layer",
            "changed_files": ["lib/storage/edge_cache.rb", "config/storage.yml"],
            "patch_diff": "+ require 'rocksdb'\n+ RocksDB.open()",
            "should_alert": True,
            "expected_conflict": "resurrected_rejected_alternative",
        },
    },
    {
        "discussion_id": "gh:encode/httpx/issues/780",
        "expected_accepted": "AnyIO",
        "expected_rejected": ["Curio"],
        "key_rejected_terms": ["curio"],
        "radar_test_pr": {
            "title": "Refactor AnyIO transport buffer",
            "changed_files": ["httpx/_transports/anyio.py"],
            "patch_diff": "- buffer = 1024\n+ buffer = 4096",
            "should_alert": False,  # Clean PR
            "expected_conflict": None,
        },
    },
    {
        "discussion_id": "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
        "expected_accepted": "pyproject.toml",
        "expected_rejected": ["YAML"],
        "key_rejected_terms": ["yaml"],
        "radar_test_pr": {
            "title": "Add external dependencies.yaml support for CI matrix",
            "changed_files": ["dependencies.yaml", "pyproject.toml"],
            "patch_diff": "+ import yaml\n+ with open('dependencies.yaml') as f: yaml.safe_load(f)",
            "should_alert": True,
            "expected_conflict": "resurrected_rejected_alternative",
        },
    },
]


def run_benchmarks() -> Dict[str, Any]:
    """Execute evaluation and compute PS06 quantitative metrics."""
    discussions = get_sample_discussions()
    pipeline = PrimordialDecisionPipeline()
    storage = DecisionStorage()
    radar = PRDecisionRadar(storage)

    total_cases = len(GROUND_TRUTH_BENCHMARKS)
    correct_accepted = 0
    total_expected_rejected = 0
    recovered_rejected = 0
    total_quotes = 0
    verified_quotes = 0
    radar_correct_alerts = 0

    benchmark_details = []

    for gt in GROUND_TRUTH_BENCHMARKS:
        disc = next((d for d in discussions if d.id == gt["discussion_id"]), None)
        if not disc:
            continue

        # Run pipeline
        res = pipeline.process_discussion(disc)
        dec = res.final_decision
        storage.save_decision(dec)

        # 1. Accepted Decision Check
        accepted_match = gt["expected_accepted"].lower() in dec.accepted_option.lower()
        if accepted_match:
            correct_accepted += 1

        # 2. Rejected Alternative Recovery Check (PS6 Core Criterion)
        extracted_rejected_names = [ra.name.lower() for ra in dec.rejected_alternatives]
        matched_gt_rejected = 0
        for exp_rej in gt["expected_rejected"]:
            total_expected_rejected += 1
            if any(exp_rej.lower() in rej_name for rej_name in extracted_rejected_names):
                recovered_rejected += 1
                matched_gt_rejected += 1

        # 3. Evidence Quote Verification Check
        for eq in dec.evidence_quotes:
            total_quotes += 1
            if eq.verified:
                verified_quotes += 1

        # 4. PR Decision Radar Warning Precision Check
        test_pr_data = gt["radar_test_pr"]
        test_pr = PullRequestDiff(
            pr_id=f"pr-eval-{disc.id}",
            title=test_pr_data["title"],
            description="",
            changed_files=test_pr_data["changed_files"],
            patch_diff=test_pr_data["patch_diff"],
        )
        alerts = radar.scan_pull_request(test_pr)

        if test_pr_data["should_alert"]:
            has_expected_alert = any(
                a.conflict_type == test_pr_data["expected_conflict"] for a in alerts
            )
            if has_expected_alert:
                radar_correct_alerts += 1
        else:
            # Clean PR shouldn't have resurrected alert
            has_resurrected_alert = any(
                a.conflict_type == "resurrected_rejected_alternative" for a in alerts
            )
            if not has_resurrected_alert:
                radar_correct_alerts += 1

        benchmark_details.append({
            "discussion_id": disc.id,
            "title": disc.title,
            "accepted_decision": dec.accepted_option,
            "accepted_correct": accepted_match,
            "expected_rejected": gt["expected_rejected"],
            "recovered_rejected_count": matched_gt_rejected,
            "quotes_count": len(dec.evidence_quotes),
            "quotes_verified_count": sum(1 for eq in dec.evidence_quotes if eq.verified),
        })

    decision_accuracy = correct_accepted / max(1, total_cases)
    rejected_recovery_rate = recovered_rejected / max(1, total_expected_rejected)
    quote_accuracy = verified_quotes / max(1, total_quotes)
    radar_precision = radar_correct_alerts / max(1, total_cases)

    return {
        "total_test_cases": total_cases,
        "decision_accuracy": round(decision_accuracy, 3),
        "rejected_recovery_rate": round(rejected_recovery_rate, 3),
        "quote_accuracy": round(quote_accuracy, 3),
        "radar_precision": round(radar_precision, 3),
        "details": benchmark_details,
    }


if __name__ == "__main__":
    results = run_benchmarks()
    print("================ PRIMORDIAL BENCHMARK EVALUATION ================")
    print(f"Accepted Decision Accuracy:    {results['decision_accuracy']*100:.1f}%")
    print(f"Rejected Recovery Rate (PS6):  {results['rejected_recovery_rate']*100:.1f}%")
    print(f"Evidence Quote Accuracy:       {results['quote_accuracy']*100:.1f}%")
    print(f"PR Decision Radar Precision:   {results['radar_precision']*100:.1f}%")
    print("=================================================================")

"""Tests for Historical PR Decision Radar."""
import os
import tempfile
import unittest

from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors.dataset_loader import get_sample_discussion_by_id
from primordial.models import PullRequestDiff
from primordial.radar.pr_scanner import PRDecisionRadar
from primordial.storage.db import DecisionStorage


class TestPRDecisionRadar(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_radar.db")
        self.storage = DecisionStorage(self.db_path)
        self.pipeline = PrimordialDecisionPipeline()

        # Seed ADR-001 (TOML accepted, YAML rejected)
        disc = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")
        dec = self.pipeline.process_discussion(disc).final_decision
        self.storage.save_decision(dec)

        self.radar = PRDecisionRadar(self.storage)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detects_resurrected_rejected_alternative(self):
        pr = PullRequestDiff(
            pr_id="PR-2041",
            title="Add YAML configuration parser for CI workflow templates",
            description="Adds PyYAML so developers can use .uv.yaml configs.",
            changed_files=["uv.yaml", "config.py"],
            patch_diff="+ import yaml\n+ yaml.safe_load(open('uv.yaml'))",
        )

        alerts = self.radar.scan_pull_request(pr)
        self.assertGreaterEqual(len(alerts), 1)

        # High severity resurrected rejected alternative
        high_alerts = [a for a in alerts if a.severity == "high"]
        self.assertEqual(len(high_alerts), 1)
        self.assertEqual(high_alerts[0].conflict_type, "resurrected_rejected_alternative")
        self.assertIn("YAML", high_alerts[0].rejected_alternative)

    def test_clean_pr_does_not_trigger_rejected_conflict(self):
        pr = PullRequestDiff(
            pr_id="PR-5010",
            title="Optimize buffer size in TOML serializer",
            description="Improves serialization throughput without altering format.",
            changed_files=["src/settings/buffer.rs"],
            patch_diff="- let size = 1024;\n+ let size = 4096;",
        )

        alerts = self.radar.scan_pull_request(pr)
        resurrected_alerts = [
            a for a in alerts if a.conflict_type == "resurrected_rejected_alternative"
        ]
        self.assertEqual(len(resurrected_alerts), 0)


if __name__ == "__main__":
    unittest.main()

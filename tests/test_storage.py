"""Tests for SQLite decision storage."""
import os
import tempfile
import unittest

from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors.dataset_loader import get_sample_discussion_by_id
from primordial.storage.db import DecisionStorage


class TestStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        self.storage = DecisionStorage(self.db_path)
        self.pipeline = PrimordialDecisionPipeline()
        self.discussion = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")
        self.decision = self.pipeline.process_discussion(self.discussion).final_decision

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_get_discussion(self):
        self.storage.save_discussion(self.discussion)
        loaded = self.storage.get_discussion(self.discussion.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, self.discussion.id)
        self.assertEqual(loaded.title, self.discussion.title)
        self.assertEqual(len(loaded.comments), len(self.discussion.comments))

    def test_save_and_get_decision(self):
        self.storage.save_decision(self.decision)
        loaded = self.storage.get_decision(self.decision.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, self.decision.id)
        self.assertEqual(loaded.status, "Accepted")
        self.assertEqual(len(loaded.rejected_alternatives), len(self.decision.rejected_alternatives))

    def test_search_decisions(self):
        self.storage.save_decision(self.decision)
        # Search by keyword in title/outcome
        res = self.storage.search_decisions(query="TOML")
        self.assertEqual(len(res), 1)

        # Search by rejected alternative name
        res_yaml = self.storage.search_decisions(query="YAML")
        self.assertEqual(len(res_yaml), 1)

        # Search by unrelated keyword
        res_none = self.storage.search_decisions(query="KubernetesClusterSetup")
        self.assertEqual(len(res_none), 0)


if __name__ == "__main__":
    unittest.main()

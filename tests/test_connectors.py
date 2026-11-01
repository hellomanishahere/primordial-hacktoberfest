"""Unit tests for GitHub and Discourse connectors."""
import unittest

from primordial.connectors.dataset_loader import (
    get_sample_discussion_by_id,
    get_sample_discussion_by_url,
    get_sample_discussions,
)
from primordial.connectors.discourse import DiscourseConnector
from primordial.connectors.github import GitHubConnector
from primordial.connectors import fetch_discussion_auto


class TestConnectors(unittest.TestCase):

    def setUp(self):
        self.gh = GitHubConnector()
        self.dc = DiscourseConnector()

    def test_github_can_handle(self):
        self.assertTrue(self.gh.can_handle("https://github.com/astral-sh/uv/issues/1042"))
        self.assertTrue(self.gh.can_handle("https://github.com/astral-sh/uv/pull/500"))
        self.assertFalse(self.gh.can_handle("https://meta.discourse.org/t/topic/123"))

    def test_github_parse_url(self):
        owner, repo, itype, num = self.gh.parse_url("https://github.com/astral-sh/uv/issues/1042")
        self.assertEqual(owner, "astral-sh")
        self.assertEqual(repo, "uv")
        self.assertEqual(itype, "issues")
        self.assertEqual(num, 1042)

    def test_discourse_can_handle(self):
        self.assertTrue(self.dc.can_handle("https://meta.discourse.org/t/embedded-cache/88219"))
        self.assertTrue(self.dc.can_handle("https://meta.discourse.org/t/88219"))
        self.assertFalse(self.dc.can_handle("https://github.com/encode/httpx/issues/780"))

    def test_discourse_parse_url(self):
        domain, slug, topic_id = self.dc.parse_url(
            "https://meta.discourse.org/t/embedded-cache-storage-engine/88219"
        )
        self.assertEqual(domain, "meta.discourse.org")
        self.assertEqual(slug, "embedded-cache-storage-engine")
        self.assertEqual(topic_id, 88219)

    def test_sample_datasets_loading(self):
        samples = get_sample_discussions()
        self.assertGreaterEqual(len(samples), 3)

        d = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")
        self.assertIsNotNone(d)
        self.assertIn("TOML", d.title)
        self.assertGreater(len(d.comments), 0)

        d2 = get_sample_discussion_by_url("https://github.com/astral-sh/uv/issues/1042")
        self.assertIsNotNone(d2)
        self.assertEqual(d.id, d2.id)

    def test_fetch_discussion_auto(self):
        d = fetch_discussion_auto("https://github.com/astral-sh/uv/issues/1042")
        self.assertIsNotNone(d)
        self.assertEqual(d.id, "gh:astral-sh/uv/issues/1042")


if __name__ == "__main__":
    unittest.main()

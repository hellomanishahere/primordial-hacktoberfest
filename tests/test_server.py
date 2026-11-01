"""Integration tests for REST API endpoints using in-memory request simulation."""
import io
import json
import unittest
from unittest.mock import MagicMock

from primordial.server.app import PrimordialAPIHandler


class DummyAPIHandler(PrimordialAPIHandler):
    """Simulates HTTP requests in-memory without opening physical network sockets."""

    def __init__(self, method: str, path: str, body: dict = None):
        self.command = method
        self.path = path
        self.request_version = "HTTP/1.1"
        self.headers = {"Host": "localhost:8080"}
        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")
            self.rfile = io.BytesIO(raw_body)
            self.headers["Content-Length"] = str(len(raw_body))
            self.headers["Content-Type"] = "application/json"
        else:
            self.rfile = io.BytesIO(b"")
        self.wfile = io.BytesIO()
        self.requestline = f"{method} {path} HTTP/1.1"
        self.server = MagicMock()
        self.client_address = ("127.0.0.1", 54321)

        if method == "GET":
            self.do_GET()
        elif method == "POST":
            self.do_POST()

    def get_json_response(self):
        output = self.wfile.getvalue()
        header_end = output.find(b"\r\n\r\n")
        if header_end != -1:
            body_bytes = output[header_end + 4 :]
        else:
            header_end = output.find(b"\n\n")
            body_bytes = output[header_end + 2 :]
        return json.loads(body_bytes.decode("utf-8"))


class TestServerEndpoints(unittest.TestCase):

    def test_health_endpoint(self):
        handler = DummyAPIHandler("GET", "/api/health")
        data = handler.get_json_response()
        self.assertEqual(data["app"], "PRIMORDIAL")
        self.assertEqual(data["status"], "healthy")
        self.assertIn("ai_engine", data)

    def test_samples_endpoint(self):
        handler = DummyAPIHandler("GET", "/api/samples")
        data = handler.get_json_response()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)

    def test_discussions_fetch_endpoint(self):
        handler = DummyAPIHandler(
            "POST",
            "/api/discussions/fetch",
            {"url": "https://github.com/astral-sh/uv/issues/1042"},
        )
        data = handler.get_json_response()
        self.assertEqual(data["id"], "gh:astral-sh/uv/issues/1042")
        self.assertIn("TOML", data["title"])

    def test_pipeline_run_endpoint(self):
        handler = DummyAPIHandler(
            "POST",
            "/api/pipeline/run",
            {"discussion_id": "gh:astral-sh/uv/issues/1042"},
        )
        data = handler.get_json_response()
        self.assertEqual(len(data["stages"]), 3)
        self.assertIn("TOML", data["final_decision"]["accepted_option"])
        self.assertGreater(len(data["final_decision"]["rejected_alternatives"]), 0)

    def test_decisions_list_and_search(self):
        # Ensure a decision is saved first
        DummyAPIHandler("POST", "/api/pipeline/run", {"discussion_id": "gh:astral-sh/uv/issues/1042"})

        handler = DummyAPIHandler("GET", "/api/decisions?q=TOML")
        data = handler.get_json_response()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_radar_scan_endpoint(self):
        # Pre-seed ADR
        DummyAPIHandler("POST", "/api/pipeline/run", {"discussion_id": "gh:astral-sh/uv/issues/1042"})

        handler = DummyAPIHandler(
            "POST",
            "/api/radar/scan",
            {
                "pr_id": "PR-test-yaml",
                "title": "Add YAML configuration parser for CI workflow templates",
                "description": "Proposing YAML format",
                "changed_files": ["uv.yaml", "config.py"],
                "patch_diff": "+ import yaml",
            },
        )
        data = handler.get_json_response()
        self.assertGreaterEqual(data["alerts_count"], 1)
        resurrected = [
            a
            for a in data["alerts"]
            if a["conflict_type"] == "resurrected_rejected_alternative"
        ]
        self.assertGreaterEqual(len(resurrected), 1)
        self.assertTrue(any(a["matched_decision_id"] == "ADR-1042" for a in resurrected))

    def test_benchmark_evaluate_endpoint(self):
        handler = DummyAPIHandler("GET", "/api/benchmark/evaluate")
        data = handler.get_json_response()
        self.assertEqual(data["rejected_recovery_rate"], 1.0)
        self.assertEqual(data["radar_precision"], 1.0)


if __name__ == "__main__":
    unittest.main()

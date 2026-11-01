"""HTTP Server and REST API for the Primordial Decision Intelligence Platform."""
from __future__ import annotations

import json
import ipaddress
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

from primordial.adr.generator import generate_madr
from primordial.ai.adapters import get_inference_adapter
from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors import fetch_discussion_auto, get_sample_discussions
from primordial.models import DecisionRecord, PullRequestDiff
from primordial.radar.pr_scanner import PRDecisionRadar
from primordial.storage.db import DecisionStorage


FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)
MAX_REQUEST_BODY_BYTES = 1_000_000
REQUEST_SOCKET_TIMEOUT_SECONDS = 10
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class RequestBodyTooLarge(ValueError):
    """Raised when a client sends a request body above the configured limit."""


class PrimordialAPIHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler serving REST APIs and frontend assets."""

    storage = DecisionStorage()
    radar = PRDecisionRadar(storage)
    pipeline = PrimordialDecisionPipeline()

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(REQUEST_SOCKET_TIMEOUT_SECONDS)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def _allow_local_request(self) -> bool:
        """Reject requests using non-loopback Host headers and cross-origin writes."""
        try:
            client_ip = ipaddress.ip_address(self.client_address[0].split("%", 1)[0])
        except ValueError:
            client_ip = None
        if client_ip is None or not client_ip.is_loopback:
            self.send_error(403, "Primordial accepts local clients only")
            return False

        host_header = self.headers.get("Host", "")
        try:
            request_host = urllib.parse.urlsplit(f"//{host_header}").hostname
        except ValueError:
            request_host = None
        if not request_host or request_host.lower() not in LOOPBACK_HOSTS:
            self.send_error(421, "Primordial accepts loopback requests only")
            return False

        origin = self.headers.get("Origin")
        if origin:
            parsed_origin = urllib.parse.urlsplit(origin)
            origin_host = (parsed_origin.hostname or "").lower()
            # Require the exact local origin that served the app. This blocks
            # browser pages on other sites from issuing state-changing requests.
            if (
                parsed_origin.scheme != "http"
                or origin_host not in LOOPBACK_HOSTS
                or parsed_origin.netloc.lower() != host_header.lower()
            ):
                self.send_error(403, "Cross-origin requests are not allowed")
                return False
        return True

    def _send_json(self, data: Any, status: int = 200) -> None:
        response_body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def _send_error_json(self, message: str, status: int = 400) -> None:
        self._send_json({"error": message, "status": status}, status=status)

    def _read_json_body(self) -> Dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid Content-Length") from exc
        if content_length < 0:
            raise ValueError("Invalid Content-Length")
        if content_length > MAX_REQUEST_BODY_BYTES:
            raise RequestBodyTooLarge("Request body exceeds the 1 MB limit")
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("JSON request body must be an object")
        return parsed

    def do_OPTIONS(self) -> None:
        if not self._allow_local_request():
            return
        # The dashboard is served from this origin, so cross-origin access is
        # neither required nor enabled.
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        if not self._allow_local_request():
            return
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. API Endpoints
        if path == "/api/health":
            adapter = get_inference_adapter()
            self._send_json({
                "status": "healthy",
                "app": "PRIMORDIAL",
                "version": "1.0.0",
                "ai_engine": adapter.get_status(),
            })
            return

        if path == "/api/samples":
            samples = get_sample_discussions()
            self._send_json([s.to_dict() for s in samples])
            return

        if path == "/api/discussions":
            discussions = self.storage.list_discussions()
            self._send_json(discussions)
            return

        if path.startswith("/api/discussions/"):
            disc_id = urllib.parse.unquote(path[len("/api/discussions/") :])
            # Check DB or samples
            disc = self.storage.get_discussion(disc_id)
            if not disc:
                # Try sample discussions
                for s in get_sample_discussions():
                    if s.id == disc_id:
                        disc = s
                        break
            if disc:
                self._send_json(disc.to_dict())
            else:
                self._send_error_json(f"Discussion '{disc_id}' not found", status=404)
            return

        if path == "/api/decisions":
            q = query.get("q", [""])[0]
            status = query.get("status", [None])[0]
            decisions = self.storage.search_decisions(query=q, status=status)
            self._send_json([d.to_dict() for d in decisions])
            return

        if path.startswith("/api/decisions/"):
            dec_id = urllib.parse.unquote(path[len("/api/decisions/") :])
            decision = self.storage.get_decision(dec_id)
            if decision:
                self._send_json(decision.to_dict())
            else:
                self._send_error_json(f"Decision '{dec_id}' not found", status=404)
            return

        if path == "/api/benchmark/evaluate":
            # Run benchmark evaluation
            from benchmarks.evaluate import run_benchmarks
            results = run_benchmarks()
            self._send_json(results)
            return

        # 2. Frontend Static Files
        self._serve_static(path)

    def do_POST(self) -> None:
        if not self._allow_local_request():
            return
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            body = self._read_json_body()
        except RequestBodyTooLarge:
            self.close_connection = True
            self._send_error_json("Request body exceeds the 1 MB limit", status=413)
            return
        except Exception:
            self._send_error_json("Malformed JSON request body", status=400)
            return

        if path == "/api/discussions/fetch":
            url_or_id = body.get("url") or body.get("id")
            if not url_or_id:
                self._send_error_json("Missing 'url' or 'id' parameter", status=400)
                return
            try:
                discussion = fetch_discussion_auto(url_or_id)
                self.storage.save_discussion(discussion)
                self._send_json(discussion.to_dict())
            except Exception:
                self._send_error_json("Could not fetch that supported public discussion", status=400)
            return

        if path == "/api/pipeline/run":
            disc_id = body.get("discussion_id")
            if not disc_id:
                self._send_error_json("Missing 'discussion_id' parameter", status=400)
                return
            try:
                discussion = self.storage.get_discussion(disc_id)
                if not discussion:
                    # Check samples
                    for s in get_sample_discussions():
                        if s.id == disc_id:
                            discussion = s
                            self.storage.save_discussion(discussion)
                            break
                if not discussion:
                    self._send_error_json(f"Discussion '{disc_id}' not found", status=404)
                    return

                # Execute 3-stage pipeline
                result = self.pipeline.process_discussion(discussion)

                # Persist decision and stage logs in database
                self.storage.save_decision(result.final_decision)
                for stage in result.stages:
                    self.storage.save_stage_log(discussion.id, stage)

                self._send_json(result.to_dict())
            except Exception:
                self._send_error_json("Pipeline execution failed", status=500)
            return

        if path == "/api/decisions":
            try:
                decision = DecisionRecord.from_dict(body)
                self.storage.save_decision(decision)
                self._send_json(decision.to_dict(), status=201)
            except Exception:
                self._send_error_json("Decision record could not be saved", status=400)
            return

        if path == "/api/radar/scan":
            try:
                pr = PullRequestDiff(
                    pr_id=body.get("pr_id", "PR-sim-01"),
                    title=body.get("title", "Simulated PR"),
                    description=body.get("description", ""),
                    changed_files=body.get("changed_files", []),
                    patch_diff=body.get("patch_diff", ""),
                )
                alerts = self.radar.scan_pull_request(pr)
                self._send_json({
                    "pr_id": pr.pr_id,
                    "title": pr.title,
                    "scanned_decisions_count": len(self.storage.list_decisions()),
                    "alerts_count": len(alerts),
                    "alerts": [a.to_dict() for a in alerts],
                })
            except Exception:
                self._send_error_json("Radar scan failed", status=500)
            return

        self._send_error_json(f"Endpoint '{path}' not found", status=404)

    def _serve_static(self, path: str) -> None:
        frontend_root = os.path.realpath(FRONTEND_DIR)
        if path in ("", "/"):
            file_path = os.path.join(frontend_root, "index.html")
        else:
            rel_path = urllib.parse.unquote(path.lstrip("/"))
            file_path = os.path.realpath(os.path.join(frontend_root, rel_path))
            if os.path.commonpath((frontend_root, file_path)) != frontend_root:
                self.send_error(404, "Not Found")
                return

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(frontend_root, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard HTTP server request noise in stdout unless in debug mode."""
        pass


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    # Pre-seed initial sample decisions in DB if empty
    storage = DecisionStorage()
    if not storage.list_decisions():
        pipeline = PrimordialDecisionPipeline()
        samples = get_sample_discussions()
        print("Initializing Primordial Decision Library with benchmark discussions...")
        for sample in samples:
            storage.save_discussion(sample)
            try:
                res = pipeline.process_discussion(sample)
                storage.save_decision(res.final_decision)
                for st in res.stages:
                    storage.save_stage_log(sample.id, st)
            except Exception as e:
                print(f"Notice: pre-seeding pipeline note for {sample.id}: {e}")

    server = HTTPServer((host, port), PrimordialAPIHandler)
    print(f"✨ PRIMORDIAL Server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down PRIMORDIAL server.")
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run_server(port=port)

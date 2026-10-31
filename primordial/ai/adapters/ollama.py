"""Ollama inference adapter for local open-weight model execution."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from primordial.ai.adapters.base import BaseInferenceAdapter


class OllamaAdapter(BaseInferenceAdapter):
    """Adapter for running open-weight models locally via Ollama."""

    # Default mapping of stage responsibilities to Ollama model tags
    STAGE_MODELS = {
        "stage1": "llama3.2:3b",
        "stage2": "phi3.5:latest",
        "stage3": "qwen2.5-coder:7b",
    }

    def __init__(self, host: Optional[str] = None, timeout: int = 45):
        self.host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.timeout = timeout

    def _make_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.host}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(data).encode("utf-8") if data else None

        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST" if data else "GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def is_available(self) -> bool:
        """Check if local Ollama daemon is active and responding."""
        try:
            res = self._make_request("api/tags")
            return "models" in res
        except Exception:
            return False

    def get_installed_models(self) -> List[str]:
        try:
            res = self._make_request("api/tags")
            return [m.get("name", "") for m in res.get("models", [])]
        except Exception:
            return []

    def get_status(self) -> Dict[str, Any]:
        available = self.is_available()
        models = self.get_installed_models() if available else []
        return {
            "adapter": "OllamaAdapter",
            "host": self.host,
            "connected": available,
            "installed_models": models,
            "required_stage_models": {
                "stage1_preprocess": "llama3.2:3b",
                "stage2_argument_mining": "phi3.5:latest",
                "stage3_decision_synthesis": "qwen2.5-coder:7b",
            },
        }

    def generate(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Execute text generation through Ollama API."""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = self._make_request("api/generate", payload)
            return response.get("response", "")
        except Exception as e:
            raise RuntimeError(
                f"Ollama generation failed for model '{model_name}' on {self.host}: {e}"
            )

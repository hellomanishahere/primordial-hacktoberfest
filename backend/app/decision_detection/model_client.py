"""Async HTTP client for Ollama LLM execution."""

import json
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.exceptions import (
    AIModelResponseException,
    AIModelTimeoutException,
    AIServiceUnavailableException,
)
from app.core.logging import get_logger

logger = get_logger("decision_detection.model_client")


class OllamaModelClient:
    """Async client communicating with a local or remote Ollama daemon."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.AI_MODEL_PRIMARY
        self.fallback_model = fallback_model or settings.AI_MODEL_FALLBACK
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else float(settings.AI_TIMEOUT_SECONDS)
        )
        self._external_client = http_client
        self._internal_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            self._internal_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=5.0)
            )
        return self._internal_client

    async def close(self) -> None:
        """Close internal HTTP client session if created."""
        if self._internal_client and not self._internal_client.is_closed:
            await self._internal_client.aclose()
            self._internal_client = None

    async def __aenter__(self) -> "OllamaModelClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:
        """Extracts and parses JSON object from model response string."""
        content = content.strip()
        # Direct JSON parse attempt
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Strip markdown fences if present (```json ... ``` or ``` ...)
        fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if fenced_match:
            try:
                return json.loads(fenced_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Substring search for outermost { ... }
        start_idx = content.find("{")
        end_idx = content.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(content[start_idx : end_idx + 1])
            except json.JSONDecodeError:
                pass

        raise AIModelResponseException(
            message="Failed to parse model response as valid JSON",
            status_code=502,
            details={"raw_content": content[:500]},
        )

    async def generate_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Executes a structured chat completion against Ollama with JSON mode enabled.

        Returns:
            Parsed JSON dictionary from the model response.
        Raises:
            AIServiceUnavailableException: Connection failure or daemon offline.
            AIModelTimeoutException: Request duration exceeded configured timeout.
            AIModelResponseException: HTTP failure or invalid/unparseable JSON.
        """
        model_name = model or self.default_model
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
            },
        }

        url = f"{self.base_url}/api/chat"
        logger.debug("Dispatching chat inference to Ollama at %s (model: %s)", url, model_name)

        try:
            response = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("Inference timed out after %ss for model %s", self.timeout_seconds, model_name)
            raise AIModelTimeoutException(
                message=f"AI model inference request timed out after {self.timeout_seconds} seconds",
                details={"model": model_name, "timeout": self.timeout_seconds},
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Ollama daemon at %s: %s", self.base_url, exc)
            raise AIServiceUnavailableException(
                message=f"Local AI service (Ollama) is unavailable at {self.base_url}. Please ensure Ollama is running.",
                details={"base_url": self.base_url, "error": str(exc)},
            ) from exc
        except Exception as exc:
            logger.error("Unexpected network error communicating with Ollama: %s", exc)
            raise AIServiceUnavailableException(
                message=f"Network error communicating with Ollama at {self.base_url}: {exc}",
                details={"base_url": self.base_url, "error": str(exc)},
            ) from exc

        if response.status_code != 200:
            logger.error("Ollama returned status code %s: %s", response.status_code, response.text[:200])
            raise AIModelResponseException(
                message=f"Ollama returned HTTP error {response.status_code}",
                status_code=502,
                details={"status_code": response.status_code, "body": response.text[:500]},
            )

        try:
            resp_json = response.json()
        except Exception as exc:
            raise AIModelResponseException(
                message="Ollama returned invalid HTTP JSON response envelope",
                status_code=502,
                details={"raw_text": response.text[:500]},
            ) from exc

        raw_message_content = resp_json.get("message", {}).get("content", "")
        if not raw_message_content:
            raise AIModelResponseException(
                message="Ollama returned empty response message content",
                status_code=502,
                details={"response_payload": resp_json},
            )

        return self._extract_json(raw_message_content)

    async def list_available_models(self) -> List[str]:
        """Queries Ollama for currently installed and available local models."""
        client = await self._get_client()
        url = f"{self.base_url}/api/tags"
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return []
        except Exception:
            return []

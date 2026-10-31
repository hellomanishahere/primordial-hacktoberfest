"""AI Inference adapters for Primordial."""
from typing import Optional

from primordial.ai.adapters.base import BaseInferenceAdapter
from primordial.ai.adapters.heuristic import HeuristicFallbackAdapter
from primordial.ai.adapters.ollama import OllamaAdapter


def get_inference_adapter(preferred: Optional[str] = None) -> BaseInferenceAdapter:
    """Return the active inference adapter.

    If preferred is specified ('ollama' or 'heuristic'), honors that preference.
    Otherwise, automatically probes Ollama and falls back to HeuristicFallbackAdapter if unavailable.
    """
    if preferred == "ollama":
        return OllamaAdapter()
    elif preferred == "heuristic":
        return HeuristicFallbackAdapter()

    ollama = OllamaAdapter()
    if ollama.is_available():
        return ollama
    return HeuristicFallbackAdapter()


__all__ = [
    "BaseInferenceAdapter",
    "OllamaAdapter",
    "HeuristicFallbackAdapter",
    "get_inference_adapter",
]

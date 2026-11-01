"""Base interface for AI inference adapters."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


def display_model_name(adapter: "BaseInferenceAdapter", configured_name: str) -> str:
    """Return the actual inference mode instead of presenting fallback code as a model."""
    if adapter.__class__.__name__ == "HeuristicFallbackAdapter":
        return "Heuristic fallback (no model inference)"
    return configured_name


class BaseInferenceAdapter(ABC):
    """Abstract interface for model execution adapters."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Execute text generation with the designated model."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend inference engine is reachable."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return engine status and available models."""
        pass

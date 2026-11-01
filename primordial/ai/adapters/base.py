"""Base interface for AI inference adapters."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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

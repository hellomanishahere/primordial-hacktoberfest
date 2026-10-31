"""Architecture Decision Record (ADR / MADR) Generation Module (Module 8)."""

from app.adr_generation.schemas import (
    ADRAlternative,
    ADRDocument,
    ADREvidenceRef,
    ADRGenerationResult,
    ADRStatus,
)
from app.adr_generation.templates import render_madr_markdown
from app.adr_generation.generator import ADRGenerator, generate_adrs
from app.adr_generation.exporter import export_adr_to_file, export_all_adrs

__all__ = [
    "ADRStatus",
    "ADREvidenceRef",
    "ADRAlternative",
    "ADRDocument",
    "ADRGenerationResult",
    "render_madr_markdown",
    "ADRGenerator",
    "generate_adrs",
    "export_adr_to_file",
    "export_all_adrs",
]

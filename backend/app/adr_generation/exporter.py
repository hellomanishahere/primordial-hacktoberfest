"""File exporter for generated ADR documents in Markdown and JSON formats (Module 8)."""

import json
import os
from typing import List

from app.adr_generation.schemas import ADRDocument, ADRGenerationResult
from app.adr_generation.templates import render_madr_markdown


def export_adr_to_file(
    adr: ADRDocument,
    output_path: str,
    format: str = "markdown",
) -> str:
    """Exports a single ADR document to specified file path in markdown or json."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if format.lower() == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(adr.to_dict(), f, indent=2, ensure_ascii=False)
    else:
        # Default to MADR markdown
        md_content = render_madr_markdown(adr)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    return output_path


def export_all_adrs(
    result: ADRGenerationResult,
    output_dir: str,
    format: str = "markdown",
) -> List[str]:
    """Exports all ADRs in the result to the destination directory using predictable filenames."""
    os.makedirs(output_dir, exist_ok=True)
    ext = "json" if format.lower() == "json" else "md"
    exported_paths: List[str] = []

    for adr in result.adrs:
        filename = f"{adr.file_slug}.{ext}"
        filepath = os.path.join(output_dir, filename)
        export_adr_to_file(adr, filepath, format=format)
        exported_paths.append(filepath)

    return exported_paths


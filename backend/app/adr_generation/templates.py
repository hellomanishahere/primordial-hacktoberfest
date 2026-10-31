"""MADR 3.0.0 compliant Markdown formatting templates for Primordial ADRs."""

from app.adr_generation.schemas import ADRDocument


def render_madr_markdown(adr: ADRDocument) -> str:
    """
    Renders an ADRDocument into standard MADR 3.0.0 format with traceable evidence.
    """
    lines = []

    # Title & Metadata
    lines.append(f"# {adr.adr_id}: {adr.title}")
    lines.append("")
    lines.append(f"* Status: **{adr.status.value.upper()}**")
    lines.append(f"* Date: {adr.date}")
    lines.append(f"* Repository: [{adr.repository}](https://github.com/{adr.repository})")
    lines.append(f"* Source Discussion: [#{adr.entity_number}]({adr.github_discussion_url})")
    lines.append("")

    # Context and Problem Statement
    lines.append("## Context and Problem Statement")
    lines.append("")
    lines.append(adr.context or "Not established in discussion.")
    lines.append("")
    if adr.problem_statement:
        lines.append(f"**Problem Statement:** {adr.problem_statement}")
        lines.append("")

    # Decision Drivers
    lines.append("## Decision Drivers")
    lines.append("")
    if adr.decision_drivers:
        for driver in adr.decision_drivers:
            lines.append(f"* {driver}")
    else:
        lines.append("* Not established in discussion.")
    lines.append("")

    # Considered Options
    lines.append("## Considered Options")
    lines.append("")
    lines.append(f"* **[Adopted]** {adr.decision}")
    if adr.considered_alternatives:
        for alt in adr.considered_alternatives:
            lines.append(f"* **[Rejected]** {alt.title}")
    lines.append("")

    # Decision Outcome
    lines.append("## Decision Outcome")
    lines.append("")
    lines.append(f"Chosen approach: **{adr.decision}**")
    lines.append("")

    # Consequences
    lines.append("### Positive Consequences")
    lines.append("")
    if adr.consequences_positive:
        for pos in adr.consequences_positive:
            lines.append(f"* {pos}")
    else:
        lines.append("* None explicitly documented in discussion.")
    lines.append("")

    lines.append("### Negative Consequences & Liabilities")
    lines.append("")
    if adr.consequences_negative:
        for neg in adr.consequences_negative:
            lines.append(f"* {neg}")
    else:
        lines.append("* None explicitly documented in discussion.")
    lines.append("")

    # Trade-offs
    lines.append("### Architectural Trade-offs")
    lines.append("")
    if adr.trade_offs:
        for tf in adr.trade_offs:
            lines.append(f"* {tf}")
    else:
        lines.append("* Not established in discussion.")
    lines.append("")

    # Pros and Cons of Considered Alternatives
    if adr.considered_alternatives:
        lines.append("## Pros and Cons of Rejected Alternatives")
        lines.append("")
        for alt in adr.considered_alternatives:
            lines.append(f"### {alt.title}")
            lines.append(f"* Status: **REJECTED** ([{alt.verification_status.upper()}])")
            lines.append(f"* Rejection Reason: {alt.rejection_reason}")
            if alt.evidence_refs:
                lines.append("* Supporting Evidence Citations:")
                for ref in alt.evidence_refs:
                    lines.append(f"  - Comment [#{ref.comment_id}]({ref.html_url}) by @{ref.author}: \"{ref.quote_snippet}\"")
            lines.append("")

    # Supporting Evidence
    lines.append("## Supporting Evidence")
    lines.append("")
    if adr.supporting_evidence:
        for ref in adr.supporting_evidence:
            lines.append(f"* **Comment [#{ref.comment_id}]({ref.html_url})** by @{ref.author} on {ref.created_at} `[{ref.verification_status.upper()}]`:")
            lines.append(f"  > \"{ref.quote_snippet}\"")
    else:
        lines.append("* No verified supporting citations recovered.")
    lines.append("")

    # Contradictory Evidence
    lines.append("## Contradictory Evidence & Objections")
    lines.append("")
    if adr.contradictory_evidence:
        for ref in adr.contradictory_evidence:
            lines.append(f"* **Comment [#{ref.comment_id}]({ref.html_url})** by @{ref.author} on {ref.created_at} `[{ref.verification_status.upper()}]`:")
            lines.append(f"  > \"{ref.quote_snippet}\"")
    else:
        lines.append("* No contradictory evidence or dissenting opinions detected in public discussion.")
    lines.append("")

    # Original GitHub Discussion Link
    lines.append("## Original GitHub Discussion")
    lines.append("")
    lines.append(f"* Direct URL: {adr.github_discussion_url}")
    lines.append("")

    return "\n".join(lines)

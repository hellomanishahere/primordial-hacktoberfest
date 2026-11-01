"""Evidence verification engine for validating extracted quotes against source discussions."""
from __future__ import annotations

import difflib
import re
from typing import List, Optional, Tuple

from primordial.models import Comment, Discussion, EvidenceQuote


def normalize_text(text: str) -> str:
    """Normalize text by stripping quotes, collapsing whitespaces, and lowercasing."""
    cleaned = re.sub(r'["\'`“”‘’]', "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def find_quote_in_text(quote: str, text: str) -> Tuple[bool, float, Optional[int], str]:
    """Search for quote in text.

    Returns:
        (is_verified, confidence_score, char_offset, context_snippet)
    """
    if not quote or not text:
        return False, 0.0, None, ""

    # 1. Exact match
    offset = text.find(quote)
    if offset != -1:
        start = max(0, offset - 40)
        end = min(len(text), offset + len(quote) + 40)
        snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
        return True, 1.0, offset, snippet

    # 2. Normalized match (ignoring case, whitespace, formatting)
    norm_quote = normalize_text(quote)
    norm_text = normalize_text(text)

    norm_offset = norm_text.find(norm_quote)
    if norm_offset != -1:
        # Approximate offset in original text
        ratio = len(text) / max(1, len(norm_text))
        approx_offset = int(norm_offset * ratio)
        start = max(0, approx_offset - 40)
        end = min(len(text), approx_offset + len(quote) + 40)
        snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
        return True, 0.95, approx_offset, snippet

    # 3. Substring fuzzy match via SequenceMatcher
    matcher = difflib.SequenceMatcher(None, norm_quote, norm_text)
    match = matcher.find_longest_match(0, len(norm_quote), 0, len(norm_text))

    if match.size >= int(len(norm_quote) * 0.75):
        confidence = round(match.size / len(norm_quote), 2)
        ratio = len(text) / max(1, len(norm_text))
        approx_offset = int(match.b * ratio)
        start = max(0, approx_offset - 40)
        end = min(len(text), approx_offset + len(quote) + 40)
        snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
        return True, confidence, approx_offset, snippet

    return False, 0.0, None, ""


def verify_evidence_quote(quote: EvidenceQuote, discussion: Discussion) -> EvidenceQuote:
    """Verify an individual evidence quote against all comments and OP in a discussion."""
    # First check target comment if specified
    all_comments = list(discussion.comments)
    # Also check OP description
    op_comment = Comment(
        id="op",
        author=discussion.author,
        created_at=discussion.created_at,
        body=discussion.description,
        url=discussion.source_url,
    )
    comments_to_search = [op_comment] + all_comments

    # Prioritize the comment_id if explicitly named
    if quote.comment_id:
        target = next((c for c in comments_to_search if c.id == quote.comment_id), None)
        if target:
            verified, conf, offset, snippet = find_quote_in_text(quote.quote, target.body)
            if verified:
                quote.verified = True
                quote.confidence = conf
                quote.char_offset = offset
                quote.context = snippet
                quote.comment_url = target.url
                quote.author = target.author
                return quote

    # Otherwise scan all comments
    for c in comments_to_search:
        verified, conf, offset, snippet = find_quote_in_text(quote.quote, c.body)
        if verified:
            quote.verified = True
            quote.confidence = conf
            quote.char_offset = offset
            quote.context = snippet
            quote.comment_id = c.id
            quote.comment_url = c.url
            quote.author = c.author
            return quote

    # Unverified
    quote.verified = False
    quote.confidence = 0.0
    return quote


def verify_evidence_quotes(
    quotes: List[EvidenceQuote], discussion: Discussion
) -> List[EvidenceQuote]:
    """Verify a list of evidence quotes against discussion contents."""
    verified_list = []
    for q in quotes:
        verified_list.append(verify_evidence_quote(q, discussion))
    return verified_list

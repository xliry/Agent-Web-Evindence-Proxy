from __future__ import annotations

import re

from awep.models import ClaimEvidence, QualityEvidence

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "with",
}


def terms(value: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{2,}", value.lower())
    return [word for word in words if word not in STOPWORDS]


def evaluate_claim_against_text(
    claim: str | None, text: str, quality: QualityEvidence
) -> ClaimEvidence | None:
    if not claim:
        return None
    if quality.status in {"blocked", "login_required", "js_required"}:
        return ClaimEvidence(text=claim, status="blocked", score=0.0)
    if quality.status == "empty":
        return ClaimEvidence(text=claim, status="empty", score=0.0)
    if quality.status == "error":
        return ClaimEvidence(text=claim, status="error", score=0.0)
    claim_terms = terms(claim)
    if not claim_terms:
        return ClaimEvidence(text=claim, status="missing", score=0.0)
    lowered = text.lower()
    matched = [term for term in claim_terms if term in lowered]
    score = len(set(matched)) / max(1, len(set(claim_terms)))
    snippet = choose_snippet(text, matched)
    if score >= 0.55 and len(set(matched)) >= min(4, len(set(claim_terms))):
        status = "supported"
    elif score >= 0.25:
        status = "weak"
    else:
        status = "missing"
    return ClaimEvidence(
        text=claim,
        status=status,
        score=round(score, 3),
        snippet=snippet,
        matched_terms=sorted(set(matched)),
    )


def choose_snippet(text: str, matched: list[str]) -> str | None:
    if not text.strip():
        return None
    lowered = text.lower()
    positions = [lowered.find(term) for term in matched if lowered.find(term) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - 220)
    end = min(len(text), center + 420)
    return " ".join(text[start:end].split())

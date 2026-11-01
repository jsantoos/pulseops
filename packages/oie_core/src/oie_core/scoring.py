"""Deterministic opportunity scoring."""

from __future__ import annotations


def clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def opportunity_score(
    *,
    financial_impact: float,
    confidence: float,
    urgency: float,
    execution_ease: float,
    impact_reference: float = 50_000.0,
) -> float:
    """Return a 0-100 ranking score.

    Financial impact is normalized to avoid letting one large currency value
    dominate every other signal. The formula is intentionally transparent.
    """

    impact = clamp01(financial_impact / impact_reference)
    score = (
        0.45 * impact
        + 0.25 * clamp01(confidence)
        + 0.20 * clamp01(urgency)
        + 0.10 * clamp01(execution_ease)
    )
    return round(score * 100.0, 2)

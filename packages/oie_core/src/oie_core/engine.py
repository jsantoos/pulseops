"""First OIE analyzer: equipment capacity opportunities."""

from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from .models import EquipmentSnapshot, Opportunity, Severity
from .scoring import opportunity_score


def _severity(utilization: float) -> Severity:
    if utilization < 0.50:
        return Severity.CRITICAL
    if utilization < 0.65:
        return Severity.HIGH
    if utilization < 0.75:
        return Severity.MEDIUM
    return Severity.LOW


def _stable_id(snapshot: EquipmentSnapshot, target: float) -> str:
    raw = f"capacity:{snapshot.equipment_id}:{target:.4f}".encode()
    return sha256(raw).hexdigest()[:16]


def analyze_capacity(
    snapshots: Iterable[EquipmentSnapshot],
    *,
    target_utilization: float = 0.80,
) -> list[Opportunity]:
    """Detect equipment under-utilization opportunities.

    Version 0 intentionally uses deterministic rules. Future predictive models
    can replace individual estimators without changing the Opportunity contract.
    """

    if not 0.0 < target_utilization <= 1.0:
        raise ValueError("target_utilization must be in (0, 1]")

    opportunities: list[Opportunity] = []

    for snapshot in snapshots:
        utilization = snapshot.utilization
        if snapshot.available_minutes <= 0 or utilization >= target_utilization:
            continue

        recoverable_minutes = max(
            int(snapshot.available_minutes * target_utilization) - snapshot.realized_minutes,
            0,
        )
        estimated_gain = recoverable_minutes * snapshot.revenue_per_realized_minute

        # Confidence is intentionally conservative in v0 because this estimate
        # is descriptive, not yet causal/predictive.
        confidence = 0.70 if snapshot.realized_minutes > 0 else 0.35
        urgency = min((target_utilization - utilization) / target_utilization + 0.5, 1.0)
        execution_ease = 0.70

        score = opportunity_score(
            financial_impact=estimated_gain,
            confidence=confidence,
            urgency=urgency,
            execution_ease=execution_ease,
        )

        opportunities.append(
            Opportunity(
                opportunity_id=_stable_id(snapshot, target_utilization),
                category="capacity",
                title=f"{snapshot.equipment_name} below target utilization",
                severity=_severity(utilization),
                confidence=confidence,
                estimated_gain=round(estimated_gain, 2),
                score=score,
                recommended_actions=(
                    "Review idle windows and compatible exam durations",
                    "Prioritize eligible patients for recovered capacity",
                ),
                evidence={
                    "equipment_id": snapshot.equipment_id,
                    "utilization": round(utilization, 4),
                    "target_utilization": target_utilization,
                    "available_minutes": snapshot.available_minutes,
                    "realized_minutes": snapshot.realized_minutes,
                    "recoverable_minutes": recoverable_minutes,
                    "revenue_per_realized_minute": round(
                        snapshot.revenue_per_realized_minute, 4
                    ),
                },
            )
        )

    return sorted(opportunities, key=lambda item: item.score, reverse=True)

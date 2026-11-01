"""Portfolio-level OIE analysis from granular operational data."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256

from .aggregation import build_equipment_snapshots
from .cancellations import summarize_cancellations
from .engine import analyze_capacity
from .models import Opportunity, Severity
from .operational_models import Appointment, AvailabilityWindow, Equipment, ExamExecution
from .scoring import opportunity_score


def analyze_operations(
    *,
    equipment: Iterable[Equipment],
    availability: Iterable[AvailabilityWindow],
    appointments: Iterable[Appointment],
    executions: Iterable[ExamExecution],
    target_utilization: float = 0.80,
    cancellation_threshold: float = 0.15,
) -> list[Opportunity]:
    """Run the deterministic M1 operational portfolio analysis."""

    equipment = tuple(equipment)
    availability = tuple(availability)
    appointments = tuple(appointments)
    executions = tuple(executions)

    snapshots = build_equipment_snapshots(
        equipment=equipment,
        availability=availability,
        appointments=appointments,
        executions=executions,
    )
    opportunities = analyze_capacity(
        snapshots,
        target_utilization=target_utilization,
    )

    equipment_names = {item.equipment_id: item.name for item in equipment}
    for summary in summarize_cancellations(appointments):
        if summary.loss_rate < cancellation_threshold:
            continue
        confidence = _cancellation_confidence(summary.total_appointments)
        urgency = min(summary.loss_rate / max(cancellation_threshold, 0.01), 1.0)
        score = opportunity_score(
            financial_impact=summary.lost_revenue,
            confidence=confidence,
            urgency=urgency,
            execution_ease=0.75,
        )
        severity = _loss_severity(summary.loss_rate)
        raw = f"cancellation:{summary.equipment_id}:{cancellation_threshold:.4f}".encode()
        opportunities.append(
            Opportunity(
                opportunity_id=sha256(raw).hexdigest()[:16],
                category="cancellation",
                title=f"{equipment_names.get(summary.equipment_id, summary.equipment_id)} cancellation/no-show loss",
                severity=severity,
                confidence=confidence,
                estimated_gain=summary.lost_revenue,
                score=score,
                recommended_actions=(
                    "Review cancellation/no-show patterns by exam type and lead time",
                    "Test targeted confirmations or wait-list recovery for high-value slots",
                ),
                evidence={
                    "equipment_id": summary.equipment_id,
                    "total_appointments": summary.total_appointments,
                    "cancelled": summary.cancelled,
                    "no_shows": summary.no_shows,
                    "loss_rate": round(summary.loss_rate, 4),
                    "lost_revenue": summary.lost_revenue,
                },
            )
        )

    publishable = [
        item
        for item in opportunities
        if item.estimated_gain > 0 and item.recommended_actions
    ]
    return sorted(publishable, key=lambda item: item.score, reverse=True)


def _cancellation_confidence(sample_size: int) -> float:
    if sample_size >= 100:
        return 0.90
    if sample_size >= 30:
        return 0.80
    if sample_size >= 10:
        return 0.70
    return 0.50


def _loss_severity(loss_rate: float) -> Severity:
    if loss_rate >= 0.30:
        return Severity.CRITICAL
    if loss_rate >= 0.20:
        return Severity.HIGH
    if loss_rate >= 0.15:
        return Severity.MEDIUM
    return Severity.LOW

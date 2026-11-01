from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Trend = Literal["improving", "worsening", "stable", "insufficient_data"]
Direction = Literal["higher_is_better", "lower_is_better", "neutral"]


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    unit: str
    direction: Direction


CATEGORY_METRICS: dict[str, tuple[MetricDefinition, ...]] = {
    "capacity": (
        MetricDefinition("utilization", "Utilização", "percent", "higher_is_better"),
        MetricDefinition("realized_minutes", "Tempo realizado", "minutes", "higher_is_better"),
        MetricDefinition("recoverable_minutes", "Capacidade recuperável", "minutes", "lower_is_better"),
        MetricDefinition("available_minutes", "Capacidade disponível", "minutes", "neutral"),
        MetricDefinition("target_utilization", "Meta de utilização", "percent", "neutral"),
        MetricDefinition(
            "revenue_per_realized_minute",
            "Receita por minuto realizado",
            "currency_per_minute",
            "neutral",
        ),
        MetricDefinition("estimated_gain", "Potencial financeiro", "currency", "lower_is_better"),
    ),
    "cancellation": (
        MetricDefinition("loss_rate", "Taxa de perda da agenda", "percent", "lower_is_better"),
        MetricDefinition("no_shows", "Ausências (no-show)", "count", "lower_is_better"),
        MetricDefinition("cancelled", "Cancelamentos", "count", "lower_is_better"),
        MetricDefinition("total_appointments", "Agendamentos analisados", "count", "neutral"),
        MetricDefinition("lost_revenue", "Receita associada às perdas", "currency", "lower_is_better"),
        MetricDefinition("estimated_gain", "Potencial financeiro", "currency", "lower_is_better"),
    ),
}


def numeric(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def metric_value(snapshot: Any, key: str) -> float | None:
    if key == "estimated_gain":
        return float(snapshot.estimated_gain)
    evidence = snapshot.evidence or {}
    return numeric(evidence.get(key))


def metric_trend(initial: float, current: float, direction: Direction) -> Trend:
    delta = current - initial
    scale = max(abs(initial), abs(current), 1.0)
    tolerance = max(scale * 0.005, 1e-9)
    if abs(delta) <= tolerance or direction == "neutral":
        return "stable"
    if direction == "higher_is_better":
        return "improving" if delta > 0 else "worsening"
    if direction == "lower_is_better":
        return "improving" if delta < 0 else "worsening"
    return "stable"


def build_metric_summary(
    snapshots: list[Any], definition: MetricDefinition
) -> dict[str, object] | None:
    values = [
        value
        for snapshot in snapshots
        if (value := metric_value(snapshot, definition.key)) is not None
    ]
    if not values:
        return None
    initial = values[0]
    current = values[-1]
    delta = current - initial
    delta_percent = (delta / abs(initial)) if initial != 0 else None
    trend: Trend = (
        metric_trend(initial, current, definition.direction)
        if len(values) >= 2
        else "insufficient_data"
    )
    return {
        "key": definition.key,
        "label": definition.label,
        "unit": definition.unit,
        "direction": definition.direction,
        "initial": initial,
        "current": current,
        "delta": delta,
        "delta_percent": delta_percent,
        "trend": trend,
    }


def history_metrics(category: str, snapshots: list[Any]) -> list[dict[str, object]]:
    definitions = CATEGORY_METRICS.get(category, ())
    return [
        summary
        for definition in definitions
        if (summary := build_metric_summary(snapshots, definition)) is not None
    ]


def overall_trend(category: str, metrics: list[dict[str, object]]) -> Trend:
    if not metrics:
        return "insufficient_data"
    primary_key = {
        "capacity": "utilization",
        "cancellation": "loss_rate",
    }.get(category)
    if primary_key:
        for metric in metrics:
            if metric["key"] == primary_key:
                return metric["trend"]  # type: ignore[return-value]
    trends = [metric["trend"] for metric in metrics]
    if "improving" in trends and "worsening" not in trends:
        return "improving"
    if "worsening" in trends and "improving" not in trends:
        return "worsening"
    if all(trend == "insufficient_data" for trend in trends):
        return "insufficient_data"
    return "stable"

PRIMARY_METRIC_BY_CATEGORY = {
    "capacity": "utilization",
    "cancellation": "loss_rate",
}


def decision_impact(
    opportunity: Any,
    snapshots: list[Any],
    outcome: Any | None,
) -> dict[str, object]:
    """Relate a recorded managerial decision to later operational snapshots.

    This is intentionally temporal/observational. It never labels the change as
    caused by the decision; it only reports whether new data exists after the
    decision and how the category's primary metric changed afterwards.
    """

    decided_at = opportunity.decided_at
    status = opportunity.status
    primary_key = PRIMARY_METRIC_BY_CATEGORY.get(opportunity.category)
    definition = next(
        (
            item
            for item in CATEGORY_METRICS.get(opportunity.category, ())
            if item.key == primary_key
        ),
        None,
    )

    if decided_at is None:
        state = "not_decided"
        before: list[Any] = []
        after: list[Any] = []
    else:
        before = [snapshot for snapshot in snapshots if snapshot.created_at <= decided_at]
        after = [snapshot for snapshot in snapshots if snapshot.created_at > decided_at]
        if status == "dismissed":
            state = "dismissed"
        elif after:
            state = "post_decision_observed"
        else:
            state = "awaiting_post_decision_data"

    baseline = None
    current = None
    delta = None
    trend: Trend = "insufficient_data"

    if definition is not None and before:
        baseline = metric_value(before[-1], definition.key)
    if definition is not None and after:
        current = metric_value(after[-1], definition.key)
    if definition is not None and baseline is not None and current is not None:
        delta = current - baseline
        trend = metric_trend(baseline, current, definition.direction)

    potential_at_decision = float(before[-1].estimated_gain) if before else None
    measured_gain = None
    outcome_notes = None
    outcome_recorded_at = None
    potential_at_outcome = None
    realization_rate = None
    if outcome is not None:
        measured_gain = outcome.measured_gain
        outcome_notes = outcome.notes
        outcome_recorded_at = outcome.created_at
        eligible = [
            snapshot for snapshot in snapshots if snapshot.created_at <= outcome.created_at
        ]
        if eligible:
            potential_at_outcome = float(eligible[-1].estimated_gain)
        if (
            measured_gain is not None
            and potential_at_outcome is not None
            and potential_at_outcome > 0
        ):
            realization_rate = float(measured_gain / potential_at_outcome)

    return {
        "state": state,
        "decision_status": status,
        "decided_at": decided_at,
        "decision_note": opportunity.decision_note,
        "snapshots_before_decision": len(before),
        "snapshots_after_decision": len(after),
        "primary_metric_key": definition.key if definition else None,
        "primary_metric_label": definition.label if definition else None,
        "primary_metric_unit": definition.unit if definition else None,
        "baseline_before_decision": baseline,
        "current_after_decision": current,
        "delta_after_decision": delta,
        "trend_after_decision": trend,
        "potential_at_decision": potential_at_decision,
        "potential_at_outcome": potential_at_outcome,
        "measured_gain": measured_gain,
        "outcome_notes": outcome_notes,
        "outcome_recorded_at": outcome_recorded_at,
        "realization_rate": realization_rate,
    }

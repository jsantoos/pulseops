from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from pulseops_api.repositories.repositories import (
    get_latest_dataset,
    list_all_opportunities,
    list_model_runs,
    list_no_show_predictions,
    list_opportunity_outcomes,
    list_opportunity_snapshots,
    no_show_measure_summary,
)
from pulseops_api.services.opportunity_history import (
    CATEGORY_METRICS,
    decision_impact,
    history_metrics,
    metric_trend,
    metric_value,
    overall_trend,
)

OPERATIONAL_CATEGORIES = {"capacity", "cancellation"}
PRIMARY_METRIC_BY_CATEGORY = {
    "capacity": "utilization",
    "cancellation": "loss_rate",
}


def _safe_rate(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _metric_current(metrics: list[dict[str, object]], key: str) -> float | None:
    for metric in metrics:
        if metric.get("key") == key:
            value = metric.get("current")
            if isinstance(value, bool):
                return None
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _numeric(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    return float(value) if isinstance(value, (int, float)) else None


def _metric_definition(category: str, key: str):
    return next(
        (definition for definition in CATEGORY_METRICS.get(category, ()) if definition.key == key),
        None,
    )


def _latest_model_summary(db: Session, organization_id: str) -> dict[str, object]:
    run = next(
        (item for item in list_model_runs(db, organization_id) if item.model_name == "no-show-risk"),
        None,
    )
    if run is None:
        return {"available": False}
    metrics = run.metrics if isinstance(run.metrics, dict) else {}
    ranking = metrics.get("selected_ranking")
    ranking = ranking if isinstance(ranking, dict) else {}
    return {
        "available": True,
        "model_version": run.selected_model_version,
        "feature_set_version": run.feature_set_version,
        "trained_at": run.created_at,
        "roc_auc": _numeric(ranking.get("roc_auc")),
        "pr_auc": _numeric(ranking.get("pr_auc")),
        "lift_at_10pct": _numeric(ranking.get("lift_at_10pct")),
        "brier_score": _numeric(ranking.get("brier_score")),
    }


def _comparison_row(
    *,
    key: str,
    label: str,
    unit: str,
    direction: str,
    current: float,
    previous: float,
    equipment_id: str | None = None,
    category: str | None = None,
) -> dict[str, object]:
    delta = current - previous
    if direction == "neutral":
        trend = "stable"
    else:
        trend = metric_trend(previous, current, direction)  # type: ignore[arg-type]
    return {
        "key": key,
        "label": label,
        "unit": unit,
        "direction": direction,
        "equipment_id": equipment_id,
        "category": category,
        "current": float(current),
        "previous": float(previous),
        "delta": float(delta),
        "delta_percent": float(delta / abs(previous)) if previous else None,
        "trend": trend,
    }


def build_executive_summary(db: Session, organization_id: str) -> dict[str, object]:
    all_items = list_all_opportunities(db, organization_id)
    operational = [item for item in all_items if item.category in OPERATIONAL_CATEGORIES]
    outcomes = list_opportunity_outcomes(db, [item.id for item in operational])

    open_items = [item for item in operational if item.status == "open"]
    accepted = [item for item in operational if item.status == "accepted"]
    measured = [item for item in operational if item.status == "measured"]
    dismissed = [item for item in operational if item.status == "dismissed"]
    decided = accepted + measured + dismissed
    adopted = accepted + measured

    measured_outcomes = [outcomes[item.id] for item in measured if item.id in outcomes]
    successful = [outcome for outcome in measured_outcomes if (outcome.measured_gain or 0.0) > 0]
    measured_gain = float(sum(outcome.measured_gain or 0.0 for outcome in measured_outcomes))

    impacts: dict[str, dict[str, object]] = {}
    snapshots_by_opportunity: dict[str, list[Any]] = {}
    measured_potential = 0.0
    equipment_rows: dict[str, dict[str, object]] = {}
    observed_after = improving_after = worsening_after = stable_after = awaiting = 0
    previous_period_candidates: list[datetime] = []

    for item in operational:
        snapshots = list_opportunity_snapshots(db, item.id)
        snapshots_by_opportunity[item.id] = snapshots
        if not snapshots:
            continue
        if len(snapshots) >= 2:
            previous_period_candidates.append(snapshots[-2].created_at)
        metrics = history_metrics(item.category, snapshots)
        trend = overall_trend(item.category, metrics)
        impact = decision_impact(item, snapshots, outcomes.get(item.id))
        impacts[item.id] = impact

        if item.status == "measured":
            basis = impact.get("potential_at_outcome")
            measured_potential += float(basis) if isinstance(basis, (int, float)) else float(item.estimated_gain)

        if item.status in {"accepted", "measured"}:
            state = impact.get("state")
            if state == "post_decision_observed":
                observed_after += 1
                post_trend = impact.get("trend_after_decision")
                if post_trend == "improving":
                    improving_after += 1
                elif post_trend == "worsening":
                    worsening_after += 1
                elif post_trend == "stable":
                    stable_after += 1
            elif state == "awaiting_post_decision_data":
                awaiting += 1

        evidence = snapshots[-1].evidence if isinstance(snapshots[-1].evidence, dict) else {}
        equipment_id = str(evidence.get("equipment_id") or "não informado")
        row = equipment_rows.setdefault(
            equipment_id,
            {
                "equipment_id": equipment_id,
                "improving": 0,
                "worsening": 0,
                "stable": 0,
                "insufficient": 0,
                "utilization": None,
                "loss_rate": None,
                "potential": 0.0,
            },
        )
        row[trend if trend in {"improving", "worsening", "stable"} else "insufficient"] += 1
        if item.category == "capacity":
            row["utilization"] = _metric_current(metrics, "utilization")
        elif item.category == "cancellation":
            row["loss_rate"] = _metric_current(metrics, "loss_rate")
        row["potential"] = float(row["potential"]) + float(item.estimated_gain)

    equipments: list[dict[str, object]] = []
    for _, row in sorted(equipment_rows.items()):
        improving = int(row["improving"])
        worsening = int(row["worsening"])
        stable = int(row["stable"])
        if worsening > 0 and improving > 0:
            state = "mixed"
        elif worsening > 0:
            state = "worsening"
        elif improving > 0:
            state = "improving"
        elif stable > 0:
            state = "stable"
        else:
            state = "insufficient_data"
        equipments.append({
            "equipment_id": row["equipment_id"],
            "state": state,
            "improving": improving,
            "worsening": worsening,
            "stable": stable,
            "utilization": row["utilization"],
            "loss_rate": row["loss_rate"],
            "potential": float(row["potential"]),
        })

    # M9.2: period-over-period comparisons are computed from immutable snapshots.
    current_potential = 0.0
    previous_potential = 0.0
    comparisons: list[dict[str, object]] = []
    have_previous = False
    for item in operational:
        snapshots = snapshots_by_opportunity.get(item.id, [])
        if not snapshots:
            continue
        current_potential += float(snapshots[-1].estimated_gain)
        previous_snapshot = snapshots[-2] if len(snapshots) >= 2 else snapshots[-1]
        previous_potential += float(previous_snapshot.estimated_gain)
        have_previous = have_previous or len(snapshots) >= 2

        if len(snapshots) < 2:
            continue
        primary_key = PRIMARY_METRIC_BY_CATEGORY.get(item.category)
        if primary_key is None:
            continue
        definition = _metric_definition(item.category, primary_key)
        if definition is None:
            continue
        previous = metric_value(snapshots[-2], primary_key)
        current = metric_value(snapshots[-1], primary_key)
        if previous is None or current is None:
            continue
        evidence = snapshots[-1].evidence if isinstance(snapshots[-1].evidence, dict) else {}
        equipment_id = str(evidence.get("equipment_id") or "não informado")
        comparisons.append(
            _comparison_row(
                key=f"{equipment_id}:{primary_key}",
                label=definition.label,
                unit=definition.unit,
                direction=definition.direction,
                current=current,
                previous=previous,
                equipment_id=equipment_id,
                category=item.category,
            )
        )

    if have_previous:
        comparisons.insert(
            0,
            _comparison_row(
                key="operational_potential",
                label="Potencial operacional monitorado",
                unit="currency",
                direction="lower_is_better",
                current=current_potential,
                previous=previous_potential,
            ),
        )

    decision_rows: list[dict[str, object]] = []
    for item in adopted:
        impact = impacts.get(item.id)
        if not impact:
            continue
        evidence = item.evidence if isinstance(item.evidence, dict) else {}
        decision_rows.append({
            "opportunity_id": item.id,
            "title": item.title,
            "equipment_id": str(evidence.get("equipment_id")) if evidence.get("equipment_id") else None,
            "category": item.category,
            "status": item.status,
            "decision_note": item.decision_note,
            "decided_at": item.decided_at,
            "primary_metric_label": impact.get("primary_metric_label"),
            "primary_metric_unit": impact.get("primary_metric_unit"),
            "baseline": impact.get("baseline_before_decision"),
            "current": impact.get("current_after_decision"),
            "delta": impact.get("delta_after_decision"),
            "trend": impact.get("trend_after_decision"),
            "snapshots_after_decision": int(impact.get("snapshots_after_decision") or 0),
        })
    decision_rows.sort(
        key=lambda row: (
            0 if row["trend"] == "worsening" else 1 if row["trend"] == "improving" else 2,
            str(row["equipment_id"] or ""),
        )
    )

    no_show = no_show_measure_summary(db, organization_id)
    active_predictions = list_no_show_predictions(db, organization_id)
    actionable_predictions = [item for item in active_predictions if item.action_recommended]

    latest_dataset = get_latest_dataset(db, organization_id)

    # Prefer unresolved opportunities. When all decisions are already made, keep the
    # executive dashboard useful by surfacing monitored opportunities that are worsening.
    unresolved = sorted(open_items, key=lambda item: item.score, reverse=True)
    if unresolved:
        priority_items = unresolved[:5]
    else:
        monitored = [
            item
            for item in adopted
            if impacts.get(item.id, {}).get("trend_after_decision") == "worsening"
            or overall_trend(item.category, history_metrics(item.category, snapshots_by_opportunity.get(item.id, []))) == "worsening"
        ]
        priority_items = sorted(monitored, key=lambda item: item.score, reverse=True)[:5]

    return {
        "generated_at": datetime.now(timezone.utc),
        "latest_dataset_at": latest_dataset.created_at if latest_dataset else None,
        "latest_dataset_status": latest_dataset.status if latest_dataset else None,
        "previous_period_at": max(previous_period_candidates) if previous_period_candidates else None,
        "opportunities": {
            "open": len(open_items),
            "in_follow_up": len(accepted),
            "measured": len(measured),
            "dismissed": len(dismissed),
            "adoption_rate": _safe_rate(len(adopted), len(decided)),
            "success_rate": _safe_rate(len(successful), len(measured)),
            "potential_identified": current_potential,
            "measured_potential": measured_potential,
            "measured_gain": measured_gain,
            "realization_rate": _safe_rate(measured_gain, measured_potential),
        },
        "decisions": {
            "observed_after_decision": observed_after,
            "improving_after_decision": improving_after,
            "worsening_after_decision": worsening_after,
            "stable_after_decision": stable_after,
            "awaiting_new_data": awaiting,
        },
        "no_show": {
            "active_predictions": len(active_predictions),
            "recommended_actions": len(actionable_predictions),
            "expected_net_value": float(sum(item.expected_net_value for item in actionable_predictions)),
            "executed_actions": int(no_show["executed_actions"]),
            "measured_outcomes": int(no_show["measured_outcomes"]),
            "pending_outcomes": int(no_show["pending_outcomes"]),
            "attendance_rate": float(no_show["attendance_rate"]),
            "no_show_rate": float(no_show["no_show_rate"]),
            "measured_recovered_value": float(no_show["measured_recovered_value"]),
        },
        "model": _latest_model_summary(db, organization_id),
        "equipments": equipments,
        "comparisons": comparisons,
        "decision_rows": decision_rows,
        "top_priorities": [
            {
                "opportunity_id": item.id,
                "title": item.title,
                "category": item.category,
                "equipment_id": (
                    str(item.evidence.get("equipment_id"))
                    if isinstance(item.evidence, dict) and item.evidence.get("equipment_id")
                    else None
                ),
                "severity": item.severity,
                "score": item.score,
                "estimated_gain": item.estimated_gain,
                "status": item.status,
            }
            for item in priority_items
        ],
    }

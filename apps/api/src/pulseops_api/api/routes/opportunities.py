from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pulseops_api.api.deps import TenantContext, require_app_request, require_min_role
from pulseops_api.core.security import Role
from pulseops_api.db.session import get_db
from pulseops_api.repositories.repositories import (
    create_audit_event,
    get_dataset,
    get_opportunity,
    get_opportunity_outcome,
    list_all_opportunities,
    list_opportunities,
    list_opportunity_outcomes,
    list_opportunity_snapshots,
    save_opportunities,
    save_outcome,
)
from pulseops_api.schemas.api import (
    AnalyzeResponse,
    OpportunityAnalyticsBreakdownRead,
    OpportunityAnalyticsRead,
    OpportunityDecisionCreate,
    OpportunityOutcomeCreate,
    OpportunityHistoryPointRead,
    OpportunityHistoryRead,
    OpportunityRead,
    OpportunityTemporalEquipmentRead,
    OpportunityTemporalRead,
    OpportunityTemporalSeriesRead,
)
from pulseops_api.services.analysis import analyze_dataset
from pulseops_api.services.opportunity_history import decision_impact, history_metrics, overall_trend
from pulseops_api.services.ingestion import parse_operational_json

router = APIRouter(tags=["opportunities"])


def _read_opportunity(opportunity, outcome=None) -> OpportunityRead:
    payload = {
        column.name: getattr(opportunity, column.name)
        for column in opportunity.__table__.columns
    }
    if outcome is not None:
        payload.update(
            measured_gain=outcome.measured_gain,
            outcome_notes=outcome.notes,
            outcome_recorded_at=outcome.created_at,
        )
    return OpportunityRead.model_validate(payload)


def _safe_rate(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _analytics_row(key: str, items: list, outcomes: dict) -> OpportunityAnalyticsBreakdownRead:
    measured = [item for item in items if item.status == "measured"]
    measured_outcomes = [outcomes[item.id] for item in measured if item.id in outcomes]
    successes = sum(1 for outcome in measured_outcomes if (outcome.measured_gain or 0.0) > 0)
    potential = float(sum(item.estimated_gain for item in items))
    measured_potential = float(sum(item.estimated_gain for item in measured))
    measured_gain = float(sum(outcome.measured_gain or 0.0 for outcome in measured_outcomes))
    return OpportunityAnalyticsBreakdownRead(
        key=key,
        opportunities=len(items),
        measured=len(measured),
        successes=successes,
        potential_identified=potential,
        measured_potential=measured_potential,
        measured_gain=measured_gain,
        success_rate=_safe_rate(successes, len(measured)),
        realization_rate=_safe_rate(measured_gain, measured_potential),
    )


@router.post(
    "/datasets/{dataset_id}/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_app_request)],
)
def analyze(
    dataset_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ANALYST)),
):
    dataset = get_dataset(db, dataset_id)
    if dataset is None or dataset.organization_id != tenant.organization_id:
        raise HTTPException(404, "dataset not found")
    operational = parse_operational_json(dataset.raw_payload)
    items = analyze_dataset(operational)
    records = save_opportunities(
        db,
        organization_id=tenant.organization_id,
        dataset_id=dataset.id,
        items=items,
    )
    dataset.status = "analyzed"
    create_audit_event(
        db, action="dataset.analyzed", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="dataset", resource_id=dataset.id,
        details={"opportunity_count": len(records)},
    )
    db.commit()
    return AnalyzeResponse(
        dataset_id=dataset.id,
        opportunity_count=len(records),
        opportunities=records,
    )


@router.get("/opportunities", response_model=list[OpportunityRead])
def get_opportunities(
    status: str = "open",
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    if status not in {"open", "accepted", "dismissed", "measured"}:
        raise HTTPException(422, "invalid opportunity status")
    items = list_opportunities(db, tenant.organization_id, status=status)
    outcomes = list_opportunity_outcomes(db, [item.id for item in items])
    return [_read_opportunity(item, outcomes.get(item.id)) for item in items]


@router.get("/opportunities/analytics", response_model=OpportunityAnalyticsRead)
def get_opportunity_analytics(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    items = list_all_opportunities(db, tenant.organization_id)
    outcomes = list_opportunity_outcomes(db, [item.id for item in items])
    measured = [item for item in items if item.status == "measured"]
    decided = [item for item in items if item.status in {"accepted", "measured", "dismissed"}]
    adopted = [item for item in items if item.status in {"accepted", "measured"}]
    measured_outcomes = [outcomes[item.id] for item in measured if item.id in outcomes]
    successes = sum(1 for outcome in measured_outcomes if (outcome.measured_gain or 0.0) > 0)
    potential = float(sum(item.estimated_gain for item in items))
    measured_potential = float(sum(item.estimated_gain for item in measured))
    measured_gain = float(sum(outcome.measured_gain or 0.0 for outcome in measured_outcomes))

    categories: dict[str, list] = {}
    equipments: dict[str, list] = {}
    for item in items:
        categories.setdefault(item.category, []).append(item)
        equipment = item.evidence.get("equipment_id") if isinstance(item.evidence, dict) else None
        equipments.setdefault(str(equipment or "não informado"), []).append(item)

    return OpportunityAnalyticsRead(
        total_opportunities=len(items),
        open_opportunities=sum(1 for item in items if item.status == "open"),
        accepted_opportunities=sum(1 for item in items if item.status == "accepted"),
        measured_opportunities=len(measured),
        dismissed_opportunities=sum(1 for item in items if item.status == "dismissed"),
        decided_opportunities=len(decided),
        adopted_opportunities=len(adopted),
        successful_opportunities=successes,
        adoption_rate=_safe_rate(len(adopted), len(decided)),
        success_rate=_safe_rate(successes, len(measured)),
        potential_identified=potential,
        measured_potential=measured_potential,
        measured_gain=measured_gain,
        realization_rate=_safe_rate(measured_gain, measured_potential),
        by_category=[_analytics_row(key, value, outcomes) for key, value in sorted(categories.items())],
        by_equipment=[_analytics_row(key, value, outcomes) for key, value in sorted(equipments.items())],
    )


@router.get(
    "/opportunities/temporal",
    response_model=OpportunityTemporalRead,
)
def get_opportunity_temporal(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    items = [
        item
        for item in list_all_opportunities(db, tenant.organization_id)
        if item.category in {"capacity", "cancellation"}
    ]
    outcomes = list_opportunity_outcomes(db, [item.id for item in items])

    grouped: dict[str, list[OpportunityTemporalSeriesRead]] = {}
    trend_totals = {
        "improving": 0,
        "worsening": 0,
        "stable": 0,
        "insufficient_data": 0,
    }

    for opportunity in items:
        snapshots = list_opportunity_snapshots(db, opportunity.id)
        if not snapshots:
            continue
        metrics = history_metrics(opportunity.category, snapshots)
        trend = overall_trend(opportunity.category, metrics)
        trend_totals[trend] += 1
        evidence = snapshots[-1].evidence or {}
        equipment_id = str(evidence.get("equipment_id") or "não informado")
        points = [
            OpportunityHistoryPointRead(
                snapshot_id=snapshot.id,
                dataset_id=snapshot.dataset_id,
                observed_at=snapshot.created_at,
                confidence=snapshot.confidence,
                estimated_gain=snapshot.estimated_gain,
                score=snapshot.score,
                severity=snapshot.severity,
                evidence=dict(snapshot.evidence),
            )
            for snapshot in snapshots
        ]
        grouped.setdefault(equipment_id, []).append(
            OpportunityTemporalSeriesRead(
                opportunity_id=opportunity.id,
                category=opportunity.category,
                title=opportunity.title,
                equipment_id=equipment_id,
                snapshot_count=len(points),
                trend=trend,
                status=opportunity.status,
                decided_at=opportunity.decided_at,
                decision_impact=decision_impact(
                    opportunity, snapshots, outcomes.get(opportunity.id)
                ),
                metrics=metrics,
                series=points,
            )
        )

    equipments = []
    for equipment_id, series in sorted(grouped.items()):
        series.sort(key=lambda item: (item.category, item.title))
        equipments.append(
            OpportunityTemporalEquipmentRead(
                equipment_id=equipment_id,
                improving=sum(1 for item in series if item.trend == "improving"),
                worsening=sum(1 for item in series if item.trend == "worsening"),
                stable=sum(1 for item in series if item.trend == "stable"),
                series=series,
            )
        )

    return OpportunityTemporalRead(
        equipment_count=len(equipments),
        series_count=sum(len(item.series) for item in equipments),
        improving=trend_totals["improving"],
        worsening=trend_totals["worsening"],
        stable=trend_totals["stable"],
        insufficient_data=trend_totals["insufficient_data"],
        equipments=equipments,
    )


@router.get(
    "/opportunities/{opportunity_id}/history",
    response_model=OpportunityHistoryRead,
)
def get_opportunity_history(
    opportunity_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    opportunity = get_opportunity(db, opportunity_id)
    if opportunity is None or opportunity.organization_id != tenant.organization_id:
        raise HTTPException(404, "opportunity not found")

    snapshots = list_opportunity_snapshots(db, opportunity.id)
    metrics = history_metrics(opportunity.category, snapshots)
    outcome = get_opportunity_outcome(db, opportunity.id)
    points = [
        OpportunityHistoryPointRead(
            snapshot_id=snapshot.id,
            dataset_id=snapshot.dataset_id,
            observed_at=snapshot.created_at,
            confidence=snapshot.confidence,
            estimated_gain=snapshot.estimated_gain,
            score=snapshot.score,
            severity=snapshot.severity,
            evidence=dict(snapshot.evidence),
        )
        for snapshot in snapshots
    ]
    return OpportunityHistoryRead(
        opportunity_id=opportunity.id,
        category=opportunity.category,
        title=opportunity.title,
        snapshot_count=len(points),
        trend=overall_trend(opportunity.category, metrics),
        decided_at=opportunity.decided_at,
        status=opportunity.status,
        decision_impact=decision_impact(opportunity, snapshots, outcome),
        metrics=metrics,
        series=points,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity_detail(
    opportunity_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    opportunity = get_opportunity(db, opportunity_id)
    if opportunity is None or opportunity.organization_id != tenant.organization_id:
        raise HTTPException(404, "opportunity not found")
    return _read_opportunity(opportunity, get_opportunity_outcome(db, opportunity.id))


@router.post(
    "/opportunities/{opportunity_id}/decision",
    response_model=OpportunityRead,
    dependencies=[Depends(require_app_request)],
)
def post_decision(
    opportunity_id: str,
    payload: OpportunityDecisionCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.MANAGER)),
):
    opportunity = get_opportunity(db, opportunity_id)
    if opportunity is None or opportunity.organization_id != tenant.organization_id:
        raise HTTPException(404, "opportunity not found")
    if opportunity.status != "open":
        raise HTTPException(409, "opportunity decision already recorded")

    opportunity.status = payload.decision
    opportunity.decision_note = payload.notes
    opportunity.decided_by = tenant.user.id
    opportunity.decided_at = datetime.now(timezone.utc)
    create_audit_event(
        db, action="opportunity.decision_recorded", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="opportunity", resource_id=opportunity.id,
        details={"decision": payload.decision, "notes": payload.notes},
    )
    db.commit()
    db.refresh(opportunity)
    return _read_opportunity(opportunity)


@router.post(
    "/opportunities/{opportunity_id}/outcome",
    status_code=201,
    dependencies=[Depends(require_app_request)],
)
def post_outcome(
    opportunity_id: str,
    payload: OpportunityOutcomeCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.MANAGER)),
):
    opportunity = get_opportunity(db, opportunity_id)
    if opportunity is None or opportunity.organization_id != tenant.organization_id:
        raise HTTPException(404, "opportunity not found")
    if opportunity.status != "accepted":
        raise HTTPException(422, "only accepted opportunities can be measured")

    outcome = save_outcome(
        db,
        opportunity_id,
        action_taken=True,
        measured_gain=payload.measured_gain,
        notes=payload.notes,
    )
    opportunity.status = "measured"
    create_audit_event(
        db, action="opportunity.outcome_recorded", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="opportunity", resource_id=opportunity.id,
        details={"action_taken": True, "measured_gain": payload.measured_gain},
    )
    db.commit()
    return {
        "id": outcome.id,
        "opportunity_id": opportunity_id,
        "status": "recorded",
    }

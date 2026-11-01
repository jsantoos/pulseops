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
    get_latest_dataset,
    get_no_show_prediction,
    list_model_runs,
    list_no_show_prediction_decisions,
    list_no_show_interventions,
    list_no_show_prediction_outcomes,
    no_show_measure_summary,
    list_no_show_predictions,
    upsert_no_show_prediction_decision,
    upsert_no_show_intervention,
    upsert_no_show_prediction_outcome,
)
from pulseops_api.schemas.api import (
    ModelRunRead,
    NoShowPredictionDecisionCreate,
    NoShowPredictionDecisionRead,
    NoShowInterventionCreate,
    NoShowInterventionRead,
    NoShowPredictionRead,
    NoShowPredictionOutcomeUpsert,
    NoShowPredictionOutcomeRead,
    NoShowMeasureSummaryRead,
    NoShowTrainResponse,
)
from pulseops_api.services.ingestion import parse_operational_json
from pulseops_api.services.no_show_ml import train_and_score_no_show

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.post(
    "/no-show/train/{dataset_id}",
    response_model=NoShowTrainResponse,
    dependencies=[Depends(require_app_request)],
)
def train_no_show(
    dataset_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ANALYST)),
):
    dataset = get_dataset(db, dataset_id)
    if dataset is None or dataset.organization_id != tenant.organization_id:
        raise HTTPException(404, "dataset not found")
    operational = parse_operational_json(dataset.raw_payload)
    try:
        run, predictions = train_and_score_no_show(
            db,
            organization_id=tenant.organization_id,
            dataset_id=dataset.id,
            dataset=operational,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    create_audit_event(
        db,
        action="ml.no_show_trained",
        organization_id=tenant.organization_id,
        user_id=tenant.user.id,
        resource_type="model_run",
        resource_id=run.id,
        details={
            "dataset_id": dataset.id,
            "selected_model_version": run.selected_model_version,
            "prediction_count": len(predictions),
        },
    )
    db.commit()
    return NoShowTrainResponse(
        model_run=run,
        prediction_count=len(predictions),
        actionable_count=sum(item.action_recommended for item in predictions),
        predictions=predictions,
    )


@router.post(
    "/no-show/train-latest",
    response_model=NoShowTrainResponse,
    dependencies=[Depends(require_app_request)],
)
def train_latest_no_show(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.ANALYST)),
):
    dataset = get_latest_dataset(db, tenant.organization_id)
    if dataset is None:
        raise HTTPException(404, "no dataset available")
    return train_no_show(dataset.id, db, tenant)


@router.get("/no-show/predictions", response_model=list[NoShowPredictionRead])
def get_no_show_predictions(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    predictions = list_no_show_predictions(db, tenant.organization_id)
    prediction_ids = [item.id for item in predictions]
    decisions = list_no_show_prediction_decisions(db, tenant.organization_id, prediction_ids)
    interventions = list_no_show_interventions(db, tenant.organization_id, prediction_ids)
    outcomes = list_no_show_prediction_outcomes(db, tenant.organization_id, prediction_ids)
    return [
        NoShowPredictionRead.model_validate(item).model_copy(
            update={
                "decision": NoShowPredictionDecisionRead.model_validate(decisions[item.id])
                if item.id in decisions else None,
                "intervention": NoShowInterventionRead.model_validate(interventions[item.id])
                if item.id in interventions else None,
                "outcome": NoShowPredictionOutcomeRead.model_validate(outcomes[item.id])
                if item.id in outcomes else None,
            }
        )
        for item in predictions
    ]


@router.post(
    "/no-show/predictions/{prediction_id}/decision",
    response_model=NoShowPredictionDecisionRead,
    dependencies=[Depends(require_app_request)],
)
def decide_no_show_prediction(
    prediction_id: str,
    payload: NoShowPredictionDecisionCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.MANAGER)),
):
    prediction = get_no_show_prediction(db, prediction_id)
    if prediction is None or prediction.organization_id != tenant.organization_id:
        raise HTTPException(404, "prediction not found")
    if prediction.recommended_action_type == "no_action" and payload.decision == "accepted":
        raise HTTPException(422, "prediction has no operational action to accept")

    result = upsert_no_show_prediction_decision(
        db,
        organization_id=tenant.organization_id,
        prediction=prediction,
        decision=payload.decision,
        note=payload.note,
        decided_by=tenant.user.id,
    )
    create_audit_event(
        db,
        action="ml.no_show_decision_recorded",
        organization_id=tenant.organization_id,
        user_id=tenant.user.id,
        resource_type="no_show_prediction",
        resource_id=prediction.id,
        details={
            "decision": payload.decision,
            "recommended_action_type": prediction.recommended_action_type,
        },
    )
    db.commit()
    db.refresh(result)
    return result


@router.put(
    "/no-show/predictions/{prediction_id}/intervention",
    response_model=NoShowInterventionRead,
    dependencies=[Depends(require_app_request)],
)
def record_no_show_intervention(
    prediction_id: str,
    payload: NoShowInterventionCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.MANAGER)),
):
    prediction = get_no_show_prediction(db, prediction_id)
    if prediction is None or prediction.organization_id != tenant.organization_id:
        raise HTTPException(404, "prediction not found")
    decisions = list_no_show_prediction_decisions(db, tenant.organization_id, [prediction.id])
    decision = decisions.get(prediction.id)
    if decision is None or decision.decision != "accepted":
        raise HTTPException(422, "only accepted recommendations can be executed")

    result = upsert_no_show_intervention(
        db,
        organization_id=tenant.organization_id,
        prediction_id=prediction.id,
        channel=payload.channel,
        contact_result=payload.contact_result,
        note=payload.note,
        executed_by=tenant.user.id,
    )
    # Keep the existing Measure representation compatible while the structured
    # intervention becomes the source of truth for execution.
    upsert_no_show_prediction_outcome(
        db,
        organization_id=tenant.organization_id,
        prediction_id=prediction.id,
        intervention_executed=True,
        observed_status=None,
        realized_revenue=None,
        measured_recovered_value=None,
        note=payload.note,
        recorded_by=tenant.user.id,
    )
    create_audit_event(
        db,
        action="ml.no_show_intervention_recorded",
        organization_id=tenant.organization_id,
        user_id=tenant.user.id,
        resource_type="no_show_prediction",
        resource_id=prediction.id,
        details={
            "channel": payload.channel,
            "contact_result": payload.contact_result,
        },
    )
    db.commit()
    db.refresh(result)
    return result


@router.put(
    "/no-show/predictions/{prediction_id}/outcome",
    response_model=NoShowPredictionOutcomeRead,
    dependencies=[Depends(require_app_request)],
)
def measure_no_show_prediction(
    prediction_id: str,
    payload: NoShowPredictionOutcomeUpsert,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.MANAGER)),
):
    prediction = get_no_show_prediction(db, prediction_id)
    if prediction is None or prediction.organization_id != tenant.organization_id:
        raise HTTPException(404, "prediction not found")
    decisions = list_no_show_prediction_decisions(db, tenant.organization_id, [prediction.id])
    decision = decisions.get(prediction.id)
    if decision is None or decision.decision != "accepted":
        raise HTTPException(422, "only accepted recommendations can be measured")

    interventions = list_no_show_interventions(db, tenant.organization_id, [prediction.id])
    if prediction.id not in interventions:
        raise HTTPException(422, "observed outcome requires a recorded intervention")

    existing_outcomes = list_no_show_prediction_outcomes(
        db, tenant.organization_id, [prediction.id]
    )
    existing_outcome = existing_outcomes.get(prediction.id)
    if (
        existing_outcome is not None
        and existing_outcome.intervention_executed
        and not payload.intervention_executed
    ):
        raise HTTPException(422, "executed intervention cannot be reverted")
    if payload.observed_status is not None and not payload.intervention_executed:
        raise HTTPException(422, "observed outcome requires an executed intervention")
    if (
        payload.observed_status is None
        and (
            payload.realized_revenue is not None
            or payload.measured_recovered_value is not None
        )
    ):
        raise HTTPException(
            422, "financial outcome values require an observed status"
        )
    scheduled_at = prediction.scheduled_at
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    if payload.observed_status is not None and scheduled_at > datetime.now(timezone.utc):
        raise HTTPException(422, "observed outcome cannot be recorded before scheduled time")

    result = upsert_no_show_prediction_outcome(
        db, organization_id=tenant.organization_id, prediction_id=prediction.id,
        intervention_executed=payload.intervention_executed,
        observed_status=payload.observed_status, realized_revenue=payload.realized_revenue,
        measured_recovered_value=payload.measured_recovered_value, note=payload.note,
        recorded_by=tenant.user.id,
    )
    create_audit_event(
        db, action="ml.no_show_outcome_recorded", organization_id=tenant.organization_id,
        user_id=tenant.user.id, resource_type="no_show_prediction", resource_id=prediction.id,
        details={"intervention_executed": payload.intervention_executed,
                 "observed_status": payload.observed_status,
                 "measured_recovered_value": payload.measured_recovered_value},
    )
    db.commit(); db.refresh(result)
    return result


@router.get("/no-show/measure-summary", response_model=NoShowMeasureSummaryRead)
def get_no_show_measure_summary(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    return no_show_measure_summary(db, tenant.organization_id)


@router.get("/model-runs", response_model=list[ModelRunRead])
def get_model_runs(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_min_role(Role.VIEWER)),
):
    return list_model_runs(db, tenant.organization_id)

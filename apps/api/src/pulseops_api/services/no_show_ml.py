from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from oie_core.models import Opportunity, Severity
from oie_core.no_show import score_future_appointments, train_no_show_model
from oie_core.scoring import opportunity_score
from pulseops_api.repositories.repositories import (
    create_model_run,
    save_no_show_predictions,
    save_opportunities,
)
from pulseops_api.services.ingestion import OperationalDataset


def train_and_score_no_show(
    db: Session,
    *,
    organization_id: str,
    dataset_id: str,
    dataset: OperationalDataset,
):
    model = train_no_show_model(list(dataset.appointments))
    predictions = score_future_appointments(
        model, list(dataset.appointments), as_of=datetime.now(timezone.utc)
    )
    report = model.report
    metrics = {
        "baseline": asdict(report.baseline_metrics),
        "challenger": asdict(report.challenger_metrics),
        "selected_ranking": asdict(report.selected_ranking_metrics),
        "validation_precision_at_0_30": report.validation_precision,
        "validation_recall_at_0_30": report.validation_recall,
    }
    run = create_model_run(
        db,
        organization_id=organization_id,
        dataset_id=dataset_id,
        model_name="no-show-risk",
        selected_model_version=report.selected_model_version,
        feature_set_version=report.feature_set_version,
        training_rows=report.training_rows,
        calibration_rows=report.calibration_rows,
        validation_rows=report.validation_rows,
        metrics=metrics,
    )
    records = save_no_show_predictions(
        db,
        organization_id=organization_id,
        dataset_id=dataset_id,
        model_run_id=run.id,
        items=predictions,
    )

    opportunities: list[Opportunity] = []
    for prediction in predictions:
        if not prediction.action_recommended or prediction.expected_net_value <= 0:
            continue
        confidence = _model_confidence(prediction.evidence.get("evidence_count", 0))
        score = opportunity_score(
            financial_impact=prediction.expected_net_value,
            confidence=confidence,
            urgency=prediction.probability,
            execution_ease=0.85,
        )
        raw = f"no-show-risk:{prediction.appointment_id}".encode()
        opportunities.append(
            Opportunity(
                opportunity_id=sha256(raw).hexdigest()[:16],
                category="no_show_risk",
                title=(
                    f"No-show risk for {prediction.equipment_id} at "
                    f"{prediction.scheduled_at.isoformat(timespec='minutes')}"
                ),
                severity=_risk_severity(prediction.probability),
                confidence=confidence,
                estimated_gain=prediction.expected_net_value,
                score=score,
                recommended_actions=(
                    "Confirm attendance using a targeted reminder",
                    "Prepare an eligible wait-list patient for slot recovery",
                ),
                evidence={
                    "appointment_id": prediction.appointment_id,
                    "equipment_id": prediction.equipment_id,
                    "exam_type": prediction.exam_type,
                    "scheduled_at": prediction.scheduled_at.isoformat(),
                    "no_show_probability": prediction.probability,
                    "expected_revenue": prediction.expected_revenue,
                    "expected_loss_without_action": prediction.expected_loss,
                    "expected_recovered_revenue": prediction.expected_recovered_revenue,
                    "expected_net_value": prediction.expected_net_value,
                    "model_version": prediction.model_version,
                    "feature_set_version": prediction.feature_set_version,
                },
            )
        )
    save_opportunities(
        db,
        organization_id=organization_id,
        dataset_id=dataset_id,
        items=opportunities,
    )
    db.commit()
    db.refresh(run)
    return run, records


def _model_confidence(evidence_count: object) -> float:
    count = int(evidence_count) if isinstance(evidence_count, int | float) else 0
    if count >= 200:
        return 0.90
    if count >= 100:
        return 0.85
    if count >= 50:
        return 0.75
    return 0.65


def _risk_severity(probability: float) -> Severity:
    if probability >= 0.75:
        return Severity.CRITICAL
    if probability >= 0.55:
        return Severity.HIGH
    if probability >= 0.35:
        return Severity.MEDIUM
    return Severity.LOW

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from oie_core.models import Opportunity
from pulseops_api.core.security import Role, normalize_email
from pulseops_api.models.db_models import (
    AuditEvent,
    Dataset,
    ModelRun,
    NoShowPrediction,
    NoShowPredictionDecision,
    NoShowIntervention,
    NoShowPredictionOutcome,
    OpportunityRecord,
    OpportunitySnapshot,
    Organization,
    OrganizationMembership,
    OutcomeRecord,
    User,
    UserSession,
)


def create_organization(db: Session, name: str) -> Organization:
    obj = Organization(name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_organization_with_owner(
    db: Session, *, name: str, user_id: str
) -> Organization:
    obj = Organization(name=name)
    db.add(obj)
    db.flush()
    membership = OrganizationMembership(
        user_id=user_id, organization_id=obj.id, role=Role.OWNER.value
    )
    db.add(membership)
    db.commit()
    db.refresh(obj)
    return obj


def get_organization(db: Session, organization_id: str) -> Organization | None:
    return db.get(Organization, organization_id)


def list_organizations(db: Session) -> list[Organization]:
    return list(db.scalars(select(Organization).order_by(Organization.created_at)))


def user_count(db: Session) -> int:
    return int(db.scalar(select(func.count(User.id))) or 0)


def create_user(
    db: Session, *, email: str, full_name: str, password_hash: str
) -> User:
    obj = User(
        email=normalize_email(email),
        full_name=full_name.strip(),
        password_hash=password_hash,
    )
    db.add(obj)
    db.flush()
    return obj


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def create_membership(
    db: Session, *, user_id: str, organization_id: str, role: Role
) -> OrganizationMembership:
    obj = OrganizationMembership(
        user_id=user_id, organization_id=organization_id, role=role.value
    )
    db.add(obj)
    db.flush()
    return obj


def get_memberships_for_user(
    db: Session, user_id: str
) -> list[OrganizationMembership]:
    stmt = (
        select(OrganizationMembership)
        .where(OrganizationMembership.user_id == user_id)
        .order_by(OrganizationMembership.created_at)
    )
    return list(db.scalars(stmt))


def get_dataset_by_content_hash(
    db: Session, *, organization_id: str, content_sha256: str
) -> Dataset | None:
    return db.scalar(
        select(Dataset).where(
            Dataset.organization_id == organization_id,
            Dataset.content_sha256 == content_sha256,
        )
    )


def create_dataset(db: Session, **values: object) -> Dataset:
    obj = Dataset(**values)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_or_create_dataset(
    db: Session, *, organization_id: str, content_sha256: str, **values: object
) -> tuple[Dataset, bool]:
    existing = get_dataset_by_content_hash(
        db, organization_id=organization_id, content_sha256=content_sha256
    )
    if existing is not None:
        return existing, True
    return create_dataset(
        db, organization_id=organization_id, content_sha256=content_sha256, **values
    ), False


def get_dataset(db: Session, dataset_id: str) -> Dataset | None:
    return db.get(Dataset, dataset_id)


def save_opportunities(
    db: Session,
    *,
    organization_id: str,
    dataset_id: str,
    items: list[Opportunity],
) -> list[OpportunityRecord]:
    """Upsert current opportunities by tenant + stable OIE identity.

    Each analysis also writes an immutable snapshot so changes across datasets
    remain auditable without flooding the Opportunity Inbox with duplicates.
    """
    records: list[OpportunityRecord] = []
    for item in items:
        if item.estimated_gain <= 0 or not item.recommended_actions:
            continue
        stmt = select(OpportunityRecord).where(
            OpportunityRecord.organization_id == organization_id,
            OpportunityRecord.oie_opportunity_id == item.opportunity_id,
        )
        record = db.scalar(stmt)
        if record is None:
            record = OpportunityRecord(
                organization_id=organization_id,
                dataset_id=dataset_id,
                oie_opportunity_id=item.opportunity_id,
                category=item.category,
                title=item.title,
                severity=item.severity.value,
                confidence=item.confidence,
                estimated_gain=item.estimated_gain,
                score=item.score,
                recommended_actions=list(item.recommended_actions),
                evidence=dict(item.evidence),
            )
            db.add(record)
            db.flush()
        else:
            record.dataset_id = dataset_id
            record.category = item.category
            record.title = item.title
            record.severity = item.severity.value
            record.confidence = item.confidence
            record.estimated_gain = item.estimated_gain
            record.score = item.score
            record.recommended_actions = list(item.recommended_actions)
            record.evidence = dict(item.evidence)

        existing_snapshot = db.scalar(
            select(OpportunitySnapshot).where(
                OpportunitySnapshot.opportunity_id == record.id,
                OpportunitySnapshot.dataset_id == dataset_id,
            )
        )
        if existing_snapshot is None:
            db.add(
                OpportunitySnapshot(
                    opportunity_id=record.id,
                    dataset_id=dataset_id,
                    confidence=item.confidence,
                    estimated_gain=item.estimated_gain,
                    score=item.score,
                    severity=item.severity.value,
                    evidence=dict(item.evidence),
                )
            )
        records.append(record)
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def list_opportunities(
    db: Session, organization_id: str, *, status: str = "open"
) -> list[OpportunityRecord]:
    stmt = (
        select(OpportunityRecord)
        .where(
            OpportunityRecord.organization_id == organization_id,
            OpportunityRecord.status == status,
        )
        .order_by(OpportunityRecord.score.desc())
    )
    return list(db.scalars(stmt))


def get_opportunity(db: Session, opportunity_id: str) -> OpportunityRecord | None:
    return db.get(OpportunityRecord, opportunity_id)


def list_opportunity_snapshots(
    db: Session, opportunity_id: str
) -> list[OpportunitySnapshot]:
    stmt = (
        select(OpportunitySnapshot)
        .where(OpportunitySnapshot.opportunity_id == opportunity_id)
        .order_by(OpportunitySnapshot.created_at.asc(), OpportunitySnapshot.id.asc())
    )
    return list(db.scalars(stmt))


def get_opportunity_outcome(db: Session, opportunity_id: str) -> OutcomeRecord | None:
    return db.scalar(
        select(OutcomeRecord).where(OutcomeRecord.opportunity_id == opportunity_id)
    )


def list_all_opportunities(db: Session, organization_id: str) -> list[OpportunityRecord]:
    stmt = (
        select(OpportunityRecord)
        .where(OpportunityRecord.organization_id == organization_id)
        .order_by(OpportunityRecord.created_at.desc())
    )
    return list(db.scalars(stmt))


def list_opportunity_outcomes(
    db: Session, opportunity_ids: list[str]
) -> dict[str, OutcomeRecord]:
    if not opportunity_ids:
        return {}
    stmt = select(OutcomeRecord).where(OutcomeRecord.opportunity_id.in_(opportunity_ids))
    return {item.opportunity_id: item for item in db.scalars(stmt)}


def save_outcome(
    db: Session,
    opportunity_id: str,
    *,
    action_taken: bool,
    measured_gain: float | None,
    notes: str | None,
) -> OutcomeRecord:
    obj = OutcomeRecord(
        opportunity_id=opportunity_id,
        action_taken=action_taken,
        measured_gain=measured_gain,
        notes=notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_user_session(
    db: Session, *, token_hash: str, user_id: str, expires_at
) -> UserSession:
    obj = UserSession(token_hash=token_hash, user_id=user_id, expires_at=expires_at)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_user_session(db: Session, token_hash: str) -> UserSession | None:
    return db.get(UserSession, token_hash)


def delete_user_session(db: Session, token_hash: str) -> None:
    obj = db.get(UserSession, token_hash)
    if obj is not None:
        db.delete(obj)
        db.commit()


def create_audit_event(
    db: Session,
    *,
    action: str,
    organization_id: str | None,
    user_id: str | None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        action=action,
        organization_id=organization_id,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(event)
    db.flush()
    return event


def list_audit_events(
    db: Session, organization_id: str, *, limit: int = 100
) -> list[AuditEvent]:
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.organization_id == organization_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(max(1, min(limit, 500)))
    )
    return list(db.scalars(stmt))


def get_latest_dataset(db: Session, organization_id: str) -> Dataset | None:
    stmt = (
        select(Dataset)
        .where(Dataset.organization_id == organization_id)
        .order_by(Dataset.created_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def create_model_run(
    db: Session,
    *,
    organization_id: str,
    dataset_id: str,
    model_name: str,
    selected_model_version: str,
    feature_set_version: str,
    training_rows: int,
    calibration_rows: int,
    validation_rows: int,
    metrics: dict[str, object],
) -> ModelRun:
    obj = ModelRun(
        organization_id=organization_id,
        dataset_id=dataset_id,
        model_name=model_name,
        selected_model_version=selected_model_version,
        feature_set_version=feature_set_version,
        training_rows=training_rows,
        calibration_rows=calibration_rows,
        validation_rows=validation_rows,
        metrics=metrics,
    )
    db.add(obj)
    db.flush()
    return obj


def save_no_show_predictions(
    db: Session, *, organization_id: str, dataset_id: str, model_run_id: str, items
) -> list[NoShowPrediction]:
    records: list[NoShowPrediction] = []
    for item in items:
        record = NoShowPrediction(
            organization_id=organization_id,
            dataset_id=dataset_id,
            model_run_id=model_run_id,
            appointment_id=item.appointment_id,
            equipment_id=item.equipment_id,
            scheduled_at=item.scheduled_at,
            probability=item.probability,
            expected_revenue=item.expected_revenue,
            expected_loss=item.expected_loss,
            expected_recovered_revenue=item.expected_recovered_revenue,
            expected_net_value=item.expected_net_value,
            action_recommended=item.action_recommended,
            recommended_action_type=item.recommended_action_type,
            recommended_action_label=item.recommended_action_label,
            recommendation_reason=item.recommendation_reason,
            risk_level=item.risk_level,
            model_version=item.model_version,
            feature_set_version=item.feature_set_version,
            evidence=dict(item.evidence),
        )
        db.add(record)
        records.append(record)
    db.flush()
    return records


def list_no_show_predictions(
    db: Session, organization_id: str, *, limit: int = 200
) -> list[NoShowPrediction]:
    """Return the operational queue from the latest no-show model run only.

    Older prediction rows are intentionally retained for model lineage and historical
    analysis, but they must never appear as duplicate active cards in the operator queue.
    """
    latest_run = db.scalar(
        select(ModelRun)
        .where(
            ModelRun.organization_id == organization_id,
            ModelRun.model_name == "no-show-risk",
        )
        .order_by(ModelRun.created_at.desc())
        .limit(1)
    )
    if latest_run is None:
        return []
    stmt = (
        select(NoShowPrediction)
        .where(
            NoShowPrediction.organization_id == organization_id,
            NoShowPrediction.model_run_id == latest_run.id,
        )
        .order_by(NoShowPrediction.probability.desc())
        .limit(max(1, min(limit, 1000)))
    )
    return list(db.scalars(stmt))


def list_model_runs(db: Session, organization_id: str, *, limit: int = 50) -> list[ModelRun]:
    stmt = (
        select(ModelRun)
        .where(ModelRun.organization_id == organization_id)
        .order_by(ModelRun.created_at.desc())
        .limit(max(1, min(limit, 200)))
    )
    return list(db.scalars(stmt))


def get_no_show_prediction(db: Session, prediction_id: str) -> NoShowPrediction | None:
    return db.get(NoShowPrediction, prediction_id)


def list_no_show_prediction_decisions(
    db: Session, organization_id: str, prediction_ids: list[str]
) -> dict[str, NoShowPredictionDecision]:
    if not prediction_ids:
        return {}
    stmt = select(NoShowPredictionDecision).where(
        NoShowPredictionDecision.organization_id == organization_id,
        NoShowPredictionDecision.prediction_id.in_(prediction_ids),
    )
    return {item.prediction_id: item for item in db.scalars(stmt)}


def upsert_no_show_prediction_decision(
    db: Session,
    *,
    organization_id: str,
    prediction: NoShowPrediction,
    decision: str,
    note: str | None,
    decided_by: str,
) -> NoShowPredictionDecision:
    existing = db.scalar(
        select(NoShowPredictionDecision).where(
            NoShowPredictionDecision.prediction_id == prediction.id
        )
    )
    if existing is None:
        existing = NoShowPredictionDecision(
            organization_id=organization_id,
            prediction_id=prediction.id,
            recommended_action_type=prediction.recommended_action_type,
            decision=decision,
            note=note,
            decided_by=decided_by,
        )
        db.add(existing)
    else:
        existing.decision = decision
        existing.note = note
        existing.decided_by = decided_by
        existing.recommended_action_type = prediction.recommended_action_type
        existing.decided_at = func.now()
    db.flush()
    return existing


def list_no_show_interventions(
    db: Session, organization_id: str, prediction_ids: list[str]
) -> dict[str, NoShowIntervention]:
    if not prediction_ids:
        return {}
    stmt = select(NoShowIntervention).where(
        NoShowIntervention.organization_id == organization_id,
        NoShowIntervention.prediction_id.in_(prediction_ids),
    )
    return {item.prediction_id: item for item in db.scalars(stmt)}


def upsert_no_show_intervention(
    db: Session,
    *,
    organization_id: str,
    prediction_id: str,
    channel: str,
    contact_result: str,
    note: str | None,
    executed_by: str,
) -> NoShowIntervention:
    existing = db.scalar(
        select(NoShowIntervention).where(
            NoShowIntervention.prediction_id == prediction_id
        )
    )
    if existing is None:
        existing = NoShowIntervention(
            organization_id=organization_id,
            prediction_id=prediction_id,
            channel=channel,
            contact_result=contact_result,
            note=note,
            executed_by=executed_by,
        )
        db.add(existing)
    else:
        existing.channel = channel
        existing.contact_result = contact_result
        existing.note = note
        existing.executed_by = executed_by
        existing.executed_at = func.now()
        existing.updated_at = func.now()
    db.flush()
    return existing


def list_no_show_prediction_outcomes(
    db: Session, organization_id: str, prediction_ids: list[str]
) -> dict[str, NoShowPredictionOutcome]:
    if not prediction_ids:
        return {}
    stmt = select(NoShowPredictionOutcome).where(
        NoShowPredictionOutcome.organization_id == organization_id,
        NoShowPredictionOutcome.prediction_id.in_(prediction_ids),
    )
    return {item.prediction_id: item for item in db.scalars(stmt)}


def upsert_no_show_prediction_outcome(
    db: Session,
    *,
    organization_id: str,
    prediction_id: str,
    intervention_executed: bool,
    observed_status: str | None,
    realized_revenue: float | None,
    measured_recovered_value: float | None,
    note: str | None,
    recorded_by: str,
) -> NoShowPredictionOutcome:
    existing = db.scalar(
        select(NoShowPredictionOutcome).where(
            NoShowPredictionOutcome.prediction_id == prediction_id
        )
    )
    if existing is None:
        existing = NoShowPredictionOutcome(
            organization_id=organization_id,
            prediction_id=prediction_id,
            intervention_executed=intervention_executed,
            observed_status=observed_status,
            realized_revenue=realized_revenue,
            measured_recovered_value=measured_recovered_value,
            note=note,
            recorded_by=recorded_by,
        )
        db.add(existing)
    else:
        existing.intervention_executed = intervention_executed
        existing.observed_status = observed_status
        existing.realized_revenue = realized_revenue
        existing.measured_recovered_value = measured_recovered_value
        existing.note = note
        existing.recorded_by = recorded_by
        existing.updated_at = func.now()
    db.flush()
    return existing


def no_show_measure_summary(db: Session, organization_id: str) -> dict[str, object]:
    decisions = list(db.scalars(select(NoShowPredictionDecision).where(
        NoShowPredictionDecision.organization_id == organization_id,
        NoShowPredictionDecision.decision == "accepted",
    )))
    interventions = list(db.scalars(select(NoShowIntervention).where(
        NoShowIntervention.organization_id == organization_id
    )))
    outcomes = list(db.scalars(select(NoShowPredictionOutcome).where(
        NoShowPredictionOutcome.organization_id == organization_id
    )))

    measured = [item for item in outcomes if item.observed_status is not None]
    attended = sum(1 for item in measured if item.observed_status == "attended")
    no_show = sum(1 for item in measured if item.observed_status == "no_show")
    cancelled = sum(1 for item in measured if item.observed_status == "cancelled")
    measured_count = len(measured)
    outcome_by_prediction = {item.prediction_id: item for item in measured}

    channel_rows: list[dict[str, object]] = []
    for channel in sorted({item.channel for item in interventions}):
        channel_interventions = [item for item in interventions if item.channel == channel]
        channel_outcomes = [
            outcome_by_prediction[item.prediction_id]
            for item in channel_interventions
            if item.prediction_id in outcome_by_prediction
        ]
        channel_rows.append({
            "channel": channel,
            "interventions": len(channel_interventions),
            "measured_outcomes": len(channel_outcomes),
            "attended": sum(1 for item in channel_outcomes if item.observed_status == "attended"),
            "no_show": sum(1 for item in channel_outcomes if item.observed_status == "no_show"),
            "cancelled": sum(1 for item in channel_outcomes if item.observed_status == "cancelled"),
            "realized_revenue": float(sum(item.realized_revenue or 0.0 for item in channel_outcomes)),
            "measured_recovered_value": float(sum(item.measured_recovered_value or 0.0 for item in channel_outcomes)),
        })

    return {
        "accepted_actions": len(decisions),
        "executed_actions": len(interventions),
        "measured_outcomes": measured_count,
        "pending_outcomes": max(len(interventions) - measured_count, 0),
        "attended": attended,
        "no_show": no_show,
        "cancelled": cancelled,
        "attendance_rate": attended / measured_count if measured_count else 0.0,
        "no_show_rate": no_show / measured_count if measured_count else 0.0,
        "cancellation_rate": cancelled / measured_count if measured_count else 0.0,
        "realized_revenue": float(sum(item.realized_revenue or 0.0 for item in measured)),
        "measured_recovered_value": float(sum(item.measured_recovered_value or 0.0 for item in measured)),
        "by_channel": channel_rows,
    }

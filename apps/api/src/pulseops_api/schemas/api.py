from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: datetime


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    filename: str
    status: str
    content_sha256: str
    created_at: datetime


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    dataset_id: str
    oie_opportunity_id: str
    category: str
    title: str
    severity: str
    confidence: float
    estimated_gain: float
    score: float
    recommended_actions: list[str]
    evidence: dict[str, Any]
    status: str
    decision_note: str | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
    measured_gain: float | None = None
    outcome_notes: str | None = None
    outcome_recorded_at: datetime | None = None
    created_at: datetime


class OpportunityHistoryPointRead(BaseModel):
    snapshot_id: str
    dataset_id: str
    observed_at: datetime
    confidence: float
    estimated_gain: float
    score: float
    severity: str
    evidence: dict[str, Any]


class OpportunityHistoryMetricRead(BaseModel):
    key: str
    label: str
    unit: str
    direction: Literal["higher_is_better", "lower_is_better", "neutral"]
    initial: float
    current: float
    delta: float
    delta_percent: float | None = None
    trend: Literal["improving", "worsening", "stable", "insufficient_data"]


class OpportunityDecisionImpactRead(BaseModel):
    state: Literal[
        "not_decided",
        "dismissed",
        "awaiting_post_decision_data",
        "post_decision_observed",
    ]
    decision_status: str
    decided_at: datetime | None = None
    decision_note: str | None = None
    snapshots_before_decision: int
    snapshots_after_decision: int
    primary_metric_key: str | None = None
    primary_metric_label: str | None = None
    primary_metric_unit: str | None = None
    baseline_before_decision: float | None = None
    current_after_decision: float | None = None
    delta_after_decision: float | None = None
    trend_after_decision: Literal["improving", "worsening", "stable", "insufficient_data"]
    potential_at_decision: float | None = None
    potential_at_outcome: float | None = None
    measured_gain: float | None = None
    outcome_notes: str | None = None
    outcome_recorded_at: datetime | None = None
    realization_rate: float | None = None


class OpportunityHistoryRead(BaseModel):
    opportunity_id: str
    category: str
    title: str
    snapshot_count: int
    trend: Literal["improving", "worsening", "stable", "insufficient_data"]
    decided_at: datetime | None = None
    status: str
    decision_impact: OpportunityDecisionImpactRead
    metrics: list[OpportunityHistoryMetricRead]
    series: list[OpportunityHistoryPointRead]


class OpportunityTemporalSeriesRead(BaseModel):
    opportunity_id: str
    category: str
    title: str
    equipment_id: str
    snapshot_count: int
    trend: Literal["improving", "worsening", "stable", "insufficient_data"]
    status: str
    decided_at: datetime | None = None
    decision_impact: OpportunityDecisionImpactRead
    metrics: list[OpportunityHistoryMetricRead]
    series: list[OpportunityHistoryPointRead]


class OpportunityTemporalEquipmentRead(BaseModel):
    equipment_id: str
    improving: int
    worsening: int
    stable: int
    series: list[OpportunityTemporalSeriesRead]


class OpportunityTemporalRead(BaseModel):
    equipment_count: int
    series_count: int
    improving: int
    worsening: int
    stable: int
    insufficient_data: int
    equipments: list[OpportunityTemporalEquipmentRead]


class OpportunityAnalyticsBreakdownRead(BaseModel):
    key: str
    opportunities: int
    measured: int
    successes: int
    potential_identified: float
    measured_potential: float
    measured_gain: float
    success_rate: float
    realization_rate: float


class OpportunityAnalyticsRead(BaseModel):
    total_opportunities: int
    open_opportunities: int
    accepted_opportunities: int
    measured_opportunities: int
    dismissed_opportunities: int
    decided_opportunities: int
    adopted_opportunities: int
    successful_opportunities: int
    adoption_rate: float
    success_rate: float
    potential_identified: float
    measured_potential: float
    measured_gain: float
    realization_rate: float
    by_category: list[OpportunityAnalyticsBreakdownRead]
    by_equipment: list[OpportunityAnalyticsBreakdownRead]


class OpportunityDecisionCreate(BaseModel):
    decision: Literal["accepted", "dismissed"]
    notes: str | None = Field(default=None, max_length=2000)


class OpportunityOutcomeCreate(BaseModel):
    measured_gain: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class AnalyzeResponse(BaseModel):
    dataset_id: str
    opportunity_count: int
    opportunities: list[OpportunityRead]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class DataIssueRead(BaseModel):
    file: str
    row: int
    field: str | None = None
    message: str
    severity: str


class DataQualityReportRead(BaseModel):
    status: str
    rows_received: int
    rows_valid: int
    rows_rejected: int
    issues: list[DataIssueRead]


class DatasetBundleRead(BaseModel):
    dataset: DatasetRead
    quality: DataQualityReportRead
    duplicate: bool = False


class LoginCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class BootstrapCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    full_name: str = Field(min_length=2, max_length=200)
    organization_name: str | None = Field(default=None, min_length=2, max_length=200)


class BootstrapStatusRead(BaseModel):
    bootstrap_required: bool


class MembershipRead(BaseModel):
    organization_id: str
    organization_name: str
    role: str


class UserRead(BaseModel):
    id: str
    email: str = Field(min_length=3, max_length=320)
    full_name: str
    memberships: list[MembershipRead]


class AuthRead(BaseModel):
    user: UserRead


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str | None
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any]
    created_at: datetime


class NoShowPredictionDecisionCreate(BaseModel):
    decision: Literal["accepted", "dismissed"]
    note: str | None = Field(default=None, max_length=2000)


class NoShowPredictionDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    prediction_id: str
    recommended_action_type: str
    decision: str
    note: str | None
    decided_by: str
    decided_at: datetime


class NoShowInterventionCreate(BaseModel):
    channel: Literal["whatsapp", "phone", "sms", "email", "other"]
    contact_result: Literal[
        "confirmed", "no_response", "cancelled", "rescheduled", "unsuccessful", "other"
    ]
    note: str | None = Field(default=None, max_length=2000)


class NoShowInterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    prediction_id: str
    channel: str
    contact_result: str
    note: str | None
    executed_by: str
    executed_at: datetime
    created_at: datetime
    updated_at: datetime


class NoShowPredictionOutcomeUpsert(BaseModel):
    intervention_executed: bool
    observed_status: Literal["attended", "no_show", "cancelled"] | None = None
    realized_revenue: float | None = Field(default=None, ge=0)
    measured_recovered_value: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=2000)


class NoShowPredictionOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    prediction_id: str
    intervention_executed: bool
    observed_status: str | None
    realized_revenue: float | None
    measured_recovered_value: float | None
    note: str | None
    recorded_by: str
    created_at: datetime
    updated_at: datetime


class NoShowChannelMeasureRead(BaseModel):
    channel: str
    interventions: int
    measured_outcomes: int
    attended: int
    no_show: int
    cancelled: int
    realized_revenue: float
    measured_recovered_value: float


class NoShowMeasureSummaryRead(BaseModel):
    accepted_actions: int
    executed_actions: int
    measured_outcomes: int
    pending_outcomes: int
    attended: int
    no_show: int
    cancelled: int
    attendance_rate: float
    no_show_rate: float
    cancellation_rate: float
    realized_revenue: float
    measured_recovered_value: float
    by_channel: list[NoShowChannelMeasureRead]


class NoShowPredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    model_run_id: str
    appointment_id: str
    equipment_id: str
    scheduled_at: datetime
    probability: float
    expected_revenue: float
    expected_loss: float
    expected_recovered_revenue: float
    expected_net_value: float
    action_recommended: bool
    recommended_action_type: str
    recommended_action_label: str
    recommendation_reason: str
    risk_level: str
    model_version: str
    feature_set_version: str
    evidence: dict[str, Any]
    decision: NoShowPredictionDecisionRead | None = None
    intervention: NoShowInterventionRead | None = None
    outcome: NoShowPredictionOutcomeRead | None = None
    created_at: datetime


class ModelRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dataset_id: str
    model_name: str
    selected_model_version: str
    feature_set_version: str
    training_rows: int
    calibration_rows: int
    validation_rows: int
    metrics: dict[str, Any]
    created_at: datetime


class NoShowTrainResponse(BaseModel):
    model_run: ModelRunRead
    prediction_count: int
    actionable_count: int
    predictions: list[NoShowPredictionRead]


class ExecutiveOpportunitySummaryRead(BaseModel):
    open: int
    in_follow_up: int
    measured: int
    dismissed: int
    adoption_rate: float
    success_rate: float
    potential_identified: float
    measured_potential: float
    measured_gain: float
    realization_rate: float


class ExecutiveDecisionSummaryRead(BaseModel):
    observed_after_decision: int
    improving_after_decision: int
    worsening_after_decision: int
    stable_after_decision: int
    awaiting_new_data: int


class ExecutiveNoShowSummaryRead(BaseModel):
    active_predictions: int
    recommended_actions: int
    expected_net_value: float
    executed_actions: int
    measured_outcomes: int
    pending_outcomes: int
    attendance_rate: float
    no_show_rate: float
    measured_recovered_value: float


class ExecutiveEquipmentRead(BaseModel):
    equipment_id: str
    state: Literal["improving", "worsening", "mixed", "stable", "insufficient_data"]
    improving: int
    worsening: int
    stable: int
    utilization: float | None = None
    loss_rate: float | None = None
    potential: float


class ExecutivePriorityRead(BaseModel):
    opportunity_id: str
    title: str
    category: str
    equipment_id: str | None = None
    severity: str
    score: float
    estimated_gain: float
    status: str


class ExecutiveComparisonRead(BaseModel):
    key: str
    label: str
    unit: str
    direction: str
    equipment_id: str | None = None
    category: str | None = None
    current: float
    previous: float
    delta: float
    delta_percent: float | None = None
    trend: Literal["improving", "worsening", "stable", "insufficient_data"]


class ExecutiveDecisionRowRead(BaseModel):
    opportunity_id: str
    title: str
    equipment_id: str | None = None
    category: str
    status: str
    decision_note: str | None = None
    decided_at: datetime | None = None
    primary_metric_label: str | None = None
    primary_metric_unit: str | None = None
    baseline: float | None = None
    current: float | None = None
    delta: float | None = None
    trend: Literal["improving", "worsening", "stable", "insufficient_data"]
    snapshots_after_decision: int


class ExecutiveModelRead(BaseModel):
    available: bool
    model_version: str | None = None
    feature_set_version: str | None = None
    trained_at: datetime | None = None
    roc_auc: float | None = None
    pr_auc: float | None = None
    lift_at_10pct: float | None = None
    brier_score: float | None = None


class ExecutiveSummaryRead(BaseModel):
    generated_at: datetime
    latest_dataset_at: datetime | None = None
    latest_dataset_status: str | None = None
    previous_period_at: datetime | None = None
    opportunities: ExecutiveOpportunitySummaryRead
    decisions: ExecutiveDecisionSummaryRead
    no_show: ExecutiveNoShowSummaryRead
    model: ExecutiveModelRead
    equipments: list[ExecutiveEquipmentRead]
    comparisons: list[ExecutiveComparisonRead]
    decision_rows: list[ExecutiveDecisionRowRead]
    top_priorities: list[ExecutivePriorityRead]

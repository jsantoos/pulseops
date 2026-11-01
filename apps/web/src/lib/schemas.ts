import { z } from "zod";

export const opportunitySchema = z.object({
  id: z.string(),
  organization_id: z.string(),
  dataset_id: z.string(),
  oie_opportunity_id: z.string(),
  category: z.string(),
  title: z.string(),
  severity: z.string(),
  confidence: z.number(),
  estimated_gain: z.number(),
  score: z.number(),
  recommended_actions: z.array(z.string()),
  evidence: z.record(z.string(), z.unknown()),
  status: z.string(),
  decision_note: z.string().nullable().optional(),
  decided_by: z.string().nullable().optional(),
  decided_at: z.string().nullable().optional(),
  measured_gain: z.number().nullable().optional(),
  outcome_notes: z.string().nullable().optional(),
  outcome_recorded_at: z.string().nullable().optional(),
  created_at: z.string(),
});

export const opportunitiesSchema = z.array(opportunitySchema);
export type Opportunity = z.infer<typeof opportunitySchema>;

export const opportunityHistoryPointSchema = z.object({
  snapshot_id: z.string(),
  dataset_id: z.string(),
  observed_at: z.string(),
  confidence: z.number(),
  estimated_gain: z.number(),
  score: z.number(),
  severity: z.string(),
  evidence: z.record(z.string(), z.unknown()),
});

export const opportunityHistoryMetricSchema = z.object({
  key: z.string(),
  label: z.string(),
  unit: z.string(),
  direction: z.enum(["higher_is_better", "lower_is_better", "neutral"]),
  initial: z.number(),
  current: z.number(),
  delta: z.number(),
  delta_percent: z.number().nullable().optional(),
  trend: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
});

export const opportunityDecisionImpactSchema = z.object({
  state: z.enum([
    "not_decided",
    "dismissed",
    "awaiting_post_decision_data",
    "post_decision_observed",
  ]),
  decision_status: z.string(),
  decided_at: z.string().nullable().optional(),
  decision_note: z.string().nullable().optional(),
  snapshots_before_decision: z.number(),
  snapshots_after_decision: z.number(),
  primary_metric_key: z.string().nullable().optional(),
  primary_metric_label: z.string().nullable().optional(),
  primary_metric_unit: z.string().nullable().optional(),
  baseline_before_decision: z.number().nullable().optional(),
  current_after_decision: z.number().nullable().optional(),
  delta_after_decision: z.number().nullable().optional(),
  trend_after_decision: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
  potential_at_decision: z.number().nullable().optional(),
  potential_at_outcome: z.number().nullable().optional(),
  measured_gain: z.number().nullable().optional(),
  outcome_notes: z.string().nullable().optional(),
  outcome_recorded_at: z.string().nullable().optional(),
  realization_rate: z.number().nullable().optional(),
});

export type OpportunityDecisionImpact = z.infer<typeof opportunityDecisionImpactSchema>;

export const opportunityHistorySchema = z.object({
  opportunity_id: z.string(),
  category: z.string(),
  title: z.string(),
  snapshot_count: z.number(),
  trend: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
  decided_at: z.string().nullable().optional(),
  status: z.string(),
  decision_impact: opportunityDecisionImpactSchema,
  metrics: z.array(opportunityHistoryMetricSchema),
  series: z.array(opportunityHistoryPointSchema),
});

export type OpportunityHistory = z.infer<typeof opportunityHistorySchema>;
export type OpportunityHistoryMetric = z.infer<typeof opportunityHistoryMetricSchema>;

export const opportunityTemporalSeriesSchema = z.object({
  opportunity_id: z.string(),
  category: z.string(),
  title: z.string(),
  equipment_id: z.string(),
  snapshot_count: z.number(),
  trend: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
  status: z.string(),
  decided_at: z.string().nullable().optional(),
  decision_impact: opportunityDecisionImpactSchema,
  metrics: z.array(opportunityHistoryMetricSchema),
  series: z.array(opportunityHistoryPointSchema),
});

export const opportunityTemporalEquipmentSchema = z.object({
  equipment_id: z.string(),
  improving: z.number(),
  worsening: z.number(),
  stable: z.number(),
  series: z.array(opportunityTemporalSeriesSchema),
});

export const opportunityTemporalSchema = z.object({
  equipment_count: z.number(),
  series_count: z.number(),
  improving: z.number(),
  worsening: z.number(),
  stable: z.number(),
  insufficient_data: z.number(),
  equipments: z.array(opportunityTemporalEquipmentSchema),
});

export type OpportunityTemporal = z.infer<typeof opportunityTemporalSchema>;
export type OpportunityTemporalSeries = z.infer<typeof opportunityTemporalSeriesSchema>;

export const opportunityAnalyticsBreakdownSchema = z.object({
  key: z.string(),
  opportunities: z.number(),
  measured: z.number(),
  successes: z.number(),
  potential_identified: z.number(),
  measured_potential: z.number(),
  measured_gain: z.number(),
  success_rate: z.number(),
  realization_rate: z.number(),
});

export const opportunityAnalyticsSchema = z.object({
  total_opportunities: z.number(),
  open_opportunities: z.number(),
  accepted_opportunities: z.number(),
  measured_opportunities: z.number(),
  dismissed_opportunities: z.number(),
  decided_opportunities: z.number(),
  adopted_opportunities: z.number(),
  successful_opportunities: z.number(),
  adoption_rate: z.number(),
  success_rate: z.number(),
  potential_identified: z.number(),
  measured_potential: z.number(),
  measured_gain: z.number(),
  realization_rate: z.number(),
  by_category: z.array(opportunityAnalyticsBreakdownSchema),
  by_equipment: z.array(opportunityAnalyticsBreakdownSchema),
});
export type OpportunityAnalytics = z.infer<typeof opportunityAnalyticsSchema>;

export const datasetBundleSchema = z.object({
  dataset: z.object({
    id: z.string(),
    organization_id: z.string(),
    filename: z.string(),
    status: z.string(),
    content_sha256: z.string(),
    created_at: z.string(),
  }),
  duplicate: z.boolean().default(false),
  quality: z.object({
    status: z.string(),
    rows_received: z.number(),
    rows_valid: z.number(),
    rows_rejected: z.number(),
    issues: z.array(
      z.object({
        file: z.string(),
        row: z.number(),
        field: z.string().nullable().optional(),
        message: z.string(),
        severity: z.string(),
      }),
    ),
  }),
});
export type DatasetBundle = z.infer<typeof datasetBundleSchema>;

export const membershipSchema = z.object({
  organization_id: z.string(),
  organization_name: z.string(),
  role: z.enum(["owner", "admin", "manager", "analyst", "viewer"]),
});

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  full_name: z.string(),
  memberships: z.array(membershipSchema),
});

export const authSchema = z.object({ user: userSchema });
export type AuthSession = z.infer<typeof authSchema>;
export type Membership = z.infer<typeof membershipSchema>;

export const bootstrapStatusSchema = z.object({ bootstrap_required: z.boolean() });


export const noShowDecisionSchema = z.object({
  id: z.string(),
  prediction_id: z.string(),
  recommended_action_type: z.string(),
  decision: z.string(),
  note: z.string().nullable(),
  decided_by: z.string(),
  decided_at: z.string(),
});
export type NoShowDecision = z.infer<typeof noShowDecisionSchema>;

export const noShowInterventionSchema = z.object({
  id: z.string(),
  prediction_id: z.string(),
  channel: z.string(),
  contact_result: z.string(),
  note: z.string().nullable(),
  executed_by: z.string(),
  executed_at: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type NoShowIntervention = z.infer<typeof noShowInterventionSchema>;

export const noShowOutcomeSchema = z.object({
  id: z.string(),
  prediction_id: z.string(),
  intervention_executed: z.boolean(),
  observed_status: z.string().nullable(),
  realized_revenue: z.number().nullable(),
  measured_recovered_value: z.number().nullable(),
  note: z.string().nullable(),
  recorded_by: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type NoShowOutcome = z.infer<typeof noShowOutcomeSchema>;

export const noShowMeasureSummarySchema = z.object({
  accepted_actions: z.number(),
  executed_actions: z.number(),
  measured_outcomes: z.number(),
  pending_outcomes: z.number(),
  attended: z.number(),
  no_show: z.number(),
  cancelled: z.number(),
  attendance_rate: z.number(),
  no_show_rate: z.number(),
  cancellation_rate: z.number(),
  realized_revenue: z.number(),
  measured_recovered_value: z.number(),
  by_channel: z.array(z.object({
    channel: z.string(),
    interventions: z.number(),
    measured_outcomes: z.number(),
    attended: z.number(),
    no_show: z.number(),
    cancelled: z.number(),
    realized_revenue: z.number(),
    measured_recovered_value: z.number(),
  })),
});
export type NoShowMeasureSummary = z.infer<typeof noShowMeasureSummarySchema>;

export const noShowPredictionSchema = z.object({
  id: z.string(),
  model_run_id: z.string(),
  appointment_id: z.string(),
  equipment_id: z.string(),
  scheduled_at: z.string(),
  probability: z.number(),
  expected_revenue: z.number(),
  expected_loss: z.number(),
  expected_recovered_revenue: z.number(),
  expected_net_value: z.number(),
  action_recommended: z.boolean(),
  recommended_action_type: z.string(),
  recommended_action_label: z.string(),
  recommendation_reason: z.string(),
  risk_level: z.string(),
  model_version: z.string(),
  feature_set_version: z.string(),
  evidence: z.record(z.string(), z.unknown()),
  decision: noShowDecisionSchema.nullable().optional(),
  intervention: noShowInterventionSchema.nullable().optional(),
  outcome: noShowOutcomeSchema.nullable().optional(),
  created_at: z.string(),
});
export const noShowPredictionsSchema = z.array(noShowPredictionSchema);
export type NoShowPrediction = z.infer<typeof noShowPredictionSchema>;

export const modelRunSchema = z.object({
  id: z.string(),
  dataset_id: z.string(),
  model_name: z.string(),
  selected_model_version: z.string(),
  feature_set_version: z.string(),
  training_rows: z.number(),
  calibration_rows: z.number(),
  validation_rows: z.number(),
  metrics: z.record(z.string(), z.unknown()),
  created_at: z.string(),
});
export const modelRunsSchema = z.array(modelRunSchema);
export type ModelRun = z.infer<typeof modelRunSchema>;

export const noShowTrainResponseSchema = z.object({
  model_run: modelRunSchema,
  prediction_count: z.number(),
  actionable_count: z.number(),
  predictions: noShowPredictionsSchema,
});
export type NoShowTrainResponse = z.infer<typeof noShowTrainResponseSchema>;


export const executiveSummarySchema = z.object({
  generated_at: z.string(),
  latest_dataset_at: z.string().nullable().optional(),
  latest_dataset_status: z.string().nullable().optional(),
  previous_period_at: z.string().nullable().optional(),
  opportunities: z.object({
    open: z.number(),
    in_follow_up: z.number(),
    measured: z.number(),
    dismissed: z.number(),
    adoption_rate: z.number(),
    success_rate: z.number(),
    potential_identified: z.number(),
    measured_potential: z.number(),
    measured_gain: z.number(),
    realization_rate: z.number(),
  }),
  decisions: z.object({
    observed_after_decision: z.number(),
    improving_after_decision: z.number(),
    worsening_after_decision: z.number(),
    stable_after_decision: z.number(),
    awaiting_new_data: z.number(),
  }),
  no_show: z.object({
    active_predictions: z.number(),
    recommended_actions: z.number(),
    expected_net_value: z.number(),
    executed_actions: z.number(),
    measured_outcomes: z.number(),
    pending_outcomes: z.number(),
    attendance_rate: z.number(),
    no_show_rate: z.number(),
    measured_recovered_value: z.number(),
  }),
  model: z.object({
    available: z.boolean(),
    model_version: z.string().nullable().optional(),
    feature_set_version: z.string().nullable().optional(),
    trained_at: z.string().nullable().optional(),
    roc_auc: z.number().nullable().optional(),
    pr_auc: z.number().nullable().optional(),
    lift_at_10pct: z.number().nullable().optional(),
    brier_score: z.number().nullable().optional(),
  }),
  equipments: z.array(z.object({
    equipment_id: z.string(),
    state: z.enum(["improving", "worsening", "mixed", "stable", "insufficient_data"]),
    improving: z.number(),
    worsening: z.number(),
    stable: z.number(),
    utilization: z.number().nullable().optional(),
    loss_rate: z.number().nullable().optional(),
    potential: z.number(),
  })),
  comparisons: z.array(z.object({
    key: z.string(),
    label: z.string(),
    unit: z.string(),
    direction: z.string(),
    equipment_id: z.string().nullable().optional(),
    category: z.string().nullable().optional(),
    current: z.number(),
    previous: z.number(),
    delta: z.number(),
    delta_percent: z.number().nullable().optional(),
    trend: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
  })),
  decision_rows: z.array(z.object({
    opportunity_id: z.string(),
    title: z.string(),
    equipment_id: z.string().nullable().optional(),
    category: z.string(),
    status: z.string(),
    decision_note: z.string().nullable().optional(),
    decided_at: z.string().nullable().optional(),
    primary_metric_label: z.string().nullable().optional(),
    primary_metric_unit: z.string().nullable().optional(),
    baseline: z.number().nullable().optional(),
    current: z.number().nullable().optional(),
    delta: z.number().nullable().optional(),
    trend: z.enum(["improving", "worsening", "stable", "insufficient_data"]),
    snapshots_after_decision: z.number(),
  })),
  top_priorities: z.array(z.object({
    opportunity_id: z.string(),
    title: z.string(),
    category: z.string(),
    equipment_id: z.string().nullable().optional(),
    severity: z.string(),
    score: z.number(),
    estimated_gain: z.number(),
    status: z.string(),
  })),
});
export type ExecutiveSummary = z.infer<typeof executiveSummarySchema>;

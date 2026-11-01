"""No-show risk training and inference for PulseOps Predict M7.

The module keeps training framework-independent and leakage-aware. Only facts
known before the appointment start are used for model features.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .calibration import PlattCalibrator
from .challengers import LogisticCancellationChallenger
from .classification import evaluate_threshold
from .decision_policy import (
    DecisionPolicy,
    InterventionEconomics,
    decide_intervention,
)
from .evaluation import ProbabilisticMetrics, evaluate_probabilities
from .features import FEATURE_SET_VERSION, CancellationFeatures, cancellation_features
from .operational_models import Appointment, AppointmentStatus
from .prediction import BayesianCancellationBaseline, Prediction
from .no_show_actions import recommend_no_show_action


class Predictor(Protocol):
    model_version: str

    def fit(self, rows: list[tuple[CancellationFeatures, int]]) -> None: ...

    def predict_one(self, features: CancellationFeatures) -> Prediction: ...


@dataclass(frozen=True, slots=True)
class RankingMetrics:
    roc_auc: float
    pr_auc: float
    lift_at_10pct: float


@dataclass(frozen=True, slots=True)
class NoShowTrainingReport:
    selected_model_version: str
    baseline_metrics: ProbabilisticMetrics
    challenger_metrics: ProbabilisticMetrics
    selected_ranking_metrics: RankingMetrics
    validation_precision: float
    validation_recall: float
    training_rows: int
    calibration_rows: int
    validation_rows: int
    feature_set_version: str = FEATURE_SET_VERSION


@dataclass(frozen=True, slots=True)
class NoShowRiskPrediction:
    appointment_id: str
    equipment_id: str
    exam_type: str
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
    evidence: dict[str, object]


@dataclass(slots=True)
class CalibratedPredictor:
    predictor: Predictor
    calibrator: PlattCalibrator

    @property
    def model_version(self) -> str:
        return f"{self.predictor.model_version}+{self.calibrator.version}"

    def fit(self, rows: list[tuple[CancellationFeatures, int]]) -> None:
        raise RuntimeError("CalibratedPredictor is assembled from separately fitted components")

    def predict_one(self, features: CancellationFeatures) -> Prediction:
        raw = self.predictor.predict_one(features)
        return Prediction(
            probability=self.calibrator.transform_one(raw.probability),
            model_version=self.model_version,
            evidence_count=raw.evidence_count,
        )


@dataclass(slots=True)
class TrainedNoShowRiskModel:
    predictor: Predictor
    report: NoShowTrainingReport

    def predict(self, appointment: Appointment) -> NoShowRiskPrediction:
        if appointment.status not in {
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        }:
            raise ValueError("only scheduled/confirmed appointments can be scored")
        features = cancellation_features(appointment)
        raw = self.predictor.predict_one(features)
        economics = InterventionEconomics(
            intervention_cost=12.0,
            success_probability=0.65,
            retained_revenue_fraction=1.0,
        )
        decision = decide_intervention(
            cancellation_probability=raw.probability,
            expected_revenue=features.expected_revenue,
            economics=economics,
            policy=DecisionPolicy(
                min_expected_net_value=50.0,
                min_risk_probability=0.20,
            ),
        )
        recommendation = recommend_no_show_action(
            probability=raw.probability,
            expected_net_value=decision.expected_net_value if decision.act else 0.0,
            expected_revenue=features.expected_revenue,
        )
        explanation = _explain_prediction(self.predictor, features, raw.probability)
        return NoShowRiskPrediction(
            appointment_id=appointment.appointment_id,
            equipment_id=appointment.equipment_id,
            exam_type=appointment.exam_type,
            scheduled_at=appointment.scheduled_start,
            probability=round(raw.probability, 6),
            expected_revenue=round(features.expected_revenue, 2),
            expected_loss=round(decision.expected_loss_without_action, 2),
            expected_recovered_revenue=round(decision.expected_recovered_revenue, 2),
            expected_net_value=round(decision.expected_net_value, 2),
            action_recommended=recommendation.actionable,
            recommended_action_type=recommendation.action_type.value,
            recommended_action_label=recommendation.label,
            recommendation_reason=recommendation.reason,
            risk_level=recommendation.risk_level,
            model_version=raw.model_version,
            feature_set_version=FEATURE_SET_VERSION,
            evidence={
                "exam_type": features.exam_type,
                "hour_of_day": features.hour_of_day,
                "day_of_week": features.day_of_week,
                "lead_time_days": round(features.lead_time_days, 2),
                "evidence_count": raw.evidence_count,
                "decision_reason": decision.reason,
                "explanation": explanation,
                "association_notice": "Os fatores descrevem associações do modelo e não estabelecem causalidade.",
            },
        )


def train_no_show_model(
    appointments: list[Appointment],
    *,
    min_labeled_rows: int = 40,
) -> TrainedNoShowRiskModel:
    """Train, calibrate and evaluate using chronological holdouts.

    The oldest 60% trains the models, the next 20% calibrates the challenger,
    and the newest 20% is untouched until final model comparison. This keeps
    future information out of both fitting and calibration.
    """
    labeled = sorted(_labeled_rows(appointments), key=lambda item: item[0].scheduled_at)
    if len(labeled) < min_labeled_rows:
        raise ValueError(
            f"at least {min_labeled_rows} completed/no-show appointments are required; "
            f"received {len(labeled)}"
        )
    train_end = max(1, int(len(labeled) * 0.60))
    calibration_end = max(train_end + 1, int(len(labeled) * 0.80))
    training = labeled[:train_end]
    calibration = labeled[train_end:calibration_end]
    validation = labeled[calibration_end:]
    if min(len(training), len(calibration), len(validation)) < 1:
        raise ValueError("not enough rows for temporal train/calibration/validation split")
    if sum(target for _, target in training) == 0:
        raise ValueError("training data must contain at least one no-show")
    if sum(target for _, target in calibration) == 0:
        raise ValueError("calibration data must contain at least one no-show")
    if sum(target for _, target in validation) == 0:
        raise ValueError("validation data must contain at least one no-show")

    baseline = BayesianCancellationBaseline()
    challenger = LogisticCancellationChallenger()
    baseline.fit(training)
    challenger.fit(training)

    calibration_targets = [target for _, target in calibration]
    calibration_probabilities = [
        challenger.predict_one(features).probability for features, _ in calibration
    ]
    calibrator = PlattCalibrator()
    calibrator.fit(calibration_probabilities, calibration_targets)
    calibrated_challenger = CalibratedPredictor(challenger, calibrator)

    y_true = [target for _, target in validation]
    baseline_prob = [baseline.predict_one(features).probability for features, _ in validation]
    challenger_prob = [
        calibrated_challenger.predict_one(features).probability
        for features, _ in validation
    ]
    baseline_metrics = evaluate_probabilities(y_true, baseline_prob)
    challenger_metrics = evaluate_probabilities(y_true, challenger_prob)

    challenger_wins = (
        challenger_metrics.brier_score < baseline_metrics.brier_score
        and challenger_metrics.log_loss <= baseline_metrics.log_loss + 0.01
        and challenger_metrics.calibration_error
        <= baseline_metrics.calibration_error + 0.03
    )
    selected: Predictor = calibrated_challenger if challenger_wins else baseline
    selected_validation_prob = challenger_prob if challenger_wins else baseline_prob
    threshold = evaluate_threshold(y_true, selected_validation_prob, threshold=0.30)
    ranking = _ranking_metrics(y_true, selected_validation_prob)

    report = NoShowTrainingReport(
        selected_model_version=selected.model_version,
        baseline_metrics=baseline_metrics,
        challenger_metrics=challenger_metrics,
        selected_ranking_metrics=ranking,
        validation_precision=threshold.precision,
        validation_recall=threshold.recall,
        training_rows=len(training),
        calibration_rows=len(calibration),
        validation_rows=len(validation),
    )
    return TrainedNoShowRiskModel(predictor=selected, report=report)


def score_future_appointments(
    model: TrainedNoShowRiskModel,
    appointments: list[Appointment],
    *,
    as_of: datetime | None = None,
) -> list[NoShowRiskPrediction]:
    candidates = [
        appointment
        for appointment in appointments
        if appointment.status
        in {AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED}
        and (as_of is None or _is_after(appointment.scheduled_start, as_of))
    ]
    predictions = [model.predict(appointment) for appointment in candidates]
    return sorted(predictions, key=lambda item: item.probability, reverse=True)


def _labeled_rows(
    appointments: list[Appointment],
) -> list[tuple[CancellationFeatures, int]]:
    rows: list[tuple[CancellationFeatures, int]] = []
    for appointment in appointments:
        if appointment.status is AppointmentStatus.NO_SHOW:
            rows.append((cancellation_features(appointment), 1))
        elif appointment.status is AppointmentStatus.COMPLETED:
            rows.append((cancellation_features(appointment), 0))
    return rows


def _ranking_metrics(y_true: list[int], y_prob: list[float]) -> RankingMetrics:
    return RankingMetrics(
        roc_auc=_roc_auc(y_true, y_prob),
        pr_auc=_pr_auc(y_true, y_prob),
        lift_at_10pct=_lift_at_k(y_true, y_prob, fraction=0.10),
    )


def _roc_auc(y_true: list[int], y_prob: list[float]) -> float:
    positives = [p for y, p in zip(y_true, y_prob, strict=True) if y == 1]
    negatives = [p for y, p in zip(y_true, y_prob, strict=True) if y == 0]
    if not positives or not negatives:
        return 0.0
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _pr_auc(y_true: list[int], y_prob: list[float]) -> float:
    positives = sum(y_true)
    if positives == 0:
        return 0.0
    ordered = sorted(zip(y_prob, y_true, strict=True), reverse=True)
    tp = fp = 0
    previous_recall = 0.0
    area = 0.0
    for _, target in ordered:
        if target == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def _lift_at_k(y_true: list[int], y_prob: list[float], *, fraction: float) -> float:
    base_rate = sum(y_true) / len(y_true)
    if base_rate <= 0:
        return 0.0
    count = max(1, round(len(y_true) * fraction))
    ordered = sorted(zip(y_prob, y_true, strict=True), reverse=True)[:count]
    top_rate = sum(target for _, target in ordered) / len(ordered)
    return top_rate / base_rate


def _explain_prediction(
    predictor: Predictor,
    features: CancellationFeatures,
    probability: float,
) -> dict[str, object]:
    """Produce local, model-supported associations without causal claims."""
    labels = {
        "hour_of_day": "Horário do agendamento",
        "day_of_week": "Dia da semana",
        "lead_time_days": "Antecedência do agendamento",
        "expected_revenue": "Valor econômico do horário",
    }
    underlying = predictor.predictor if isinstance(predictor, CalibratedPredictor) else predictor
    if isinstance(underlying, LogisticCancellationChallenger):
        contributions = underlying.feature_contributions(features)
        ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:3]
        factors = [
            {
                "feature": name,
                "label": labels[name],
                "direction": "increase" if contribution >= 0 else "decrease",
                "strength": round(abs(contribution), 4),
            }
            for name, contribution in ranked
            if abs(contribution) > 1e-8
        ]
        return {
            "method": "local_logistic_contribution",
            "summary": "Principais associações locais usadas pelo modelo logístico para este agendamento.",
            "factors": factors,
            "probability": round(probability, 6),
        }
    if isinstance(underlying, BayesianCancellationBaseline):
        exam_probability, global_rate, count = underlying.exam_type_signal(features)
        direction = "increase" if exam_probability >= global_rate else "decrease"
        return {
            "method": "empirical_exam_type_rate",
            "summary": "O baseline usa a taxa histórica suavizada do tipo de exame.",
            "factors": [
                {
                    "feature": "exam_type",
                    "label": f"Tipo de exame: {features.exam_type}",
                    "direction": direction,
                    "strength": round(abs(exam_probability - global_rate), 4),
                    "evidence_count": count,
                }
            ],
            "probability": round(probability, 6),
        }
    return {"method": "unavailable", "summary": "Explicação local indisponível.", "factors": []}


def _is_after(value: datetime, reference: datetime) -> bool:
    """Compare aware/naive datetimes without silently changing wall-clock semantics."""
    if value.tzinfo is None and reference.tzinfo is not None:
        reference = reference.replace(tzinfo=None)
    elif value.tzinfo is not None and reference.tzinfo is None:
        reference = reference.replace(tzinfo=value.tzinfo)
    return value > reference

from datetime import datetime, timedelta

import pytest

from oie_core.challengers import LogisticCancellationChallenger
from oie_core.classification import evaluate_threshold
from oie_core.decision_policy import (
    DecisionPolicy,
    InterventionEconomics,
    decide_intervention,
)
from oie_core.evaluation import ProbabilisticMetrics
from oie_core.features import cancellation_features
from oie_core.model_governance import PromotionPolicy, evaluate_promotion
from oie_core.operational_models import Appointment, AppointmentStatus


def make_row(index: int, target: int) -> tuple:
    scheduled = datetime(2026, 1, 1) + timedelta(days=index)
    # Synthetic learnable pattern: long lead time and late-day appointments
    # carry higher cancellation risk.
    lead_days = 20 if target else 2
    hour = 17 if target else 9
    appointment = Appointment(
        appointment_id=f"m3-{index}",
        equipment_id="rm-01",
        exam_type="MRI",
        scheduled_start=scheduled.replace(hour=hour),
        scheduled_duration_minutes=60,
        status=AppointmentStatus.CANCELLED if target else AppointmentStatus.COMPLETED,
        expected_revenue=1500.0,
        created_at=scheduled.replace(hour=hour) - timedelta(days=lead_days),
    )
    return cancellation_features(appointment), target


def test_logistic_challenger_learns_numeric_signal() -> None:
    rows = [make_row(i, i % 3 == 0) for i in range(60)]
    model = LogisticCancellationChallenger(epochs=500)
    model.fit(rows)
    risky = model.predict_one(make_row(100, 1)[0])
    safe = model.predict_one(make_row(101, 0)[0])
    assert risky.probability > safe.probability
    assert 0 <= safe.probability <= 1
    assert risky.evidence_count == 60


def test_promotion_requires_material_improvement_and_no_safety_regression() -> None:
    champion = ProbabilisticMetrics(0.20, 0.60, 0.08, 0.2, 100)
    challenger = ProbabilisticMetrics(0.18, 0.59, 0.07, 0.2, 100)
    decision = evaluate_promotion(champion, challenger)
    assert decision.promote

    poorly_calibrated = ProbabilisticMetrics(0.18, 0.59, 0.20, 0.2, 100)
    rejected = evaluate_promotion(champion, poorly_calibrated)
    assert not rejected.promote
    assert any("calibration" in reason for reason in rejected.reasons)


def test_promotion_rejects_tiny_validation_set() -> None:
    metrics = ProbabilisticMetrics(0.1, 0.3, 0.02, 0.2, 10)
    decision = evaluate_promotion(
        ProbabilisticMetrics(0.2, 0.5, 0.05, 0.2, 10),
        metrics,
        PromotionPolicy(min_validation_samples=30),
    )
    assert not decision.promote


def test_decision_policy_acts_only_when_expected_value_is_positive() -> None:
    economics = InterventionEconomics(
        intervention_cost=20.0,
        success_probability=0.5,
        retained_revenue_fraction=1.0,
    )
    high_value = decide_intervention(
        cancellation_probability=0.4,
        expected_revenue=2000.0,
        economics=economics,
    )
    assert high_value.act
    assert high_value.expected_net_value == pytest.approx(380.0)

    low_value = decide_intervention(
        cancellation_probability=0.1,
        expected_revenue=100.0,
        economics=economics,
        policy=DecisionPolicy(min_expected_net_value=1.0),
    )
    assert not low_value.act


def test_threshold_metrics_are_explicit() -> None:
    metrics = evaluate_threshold([0, 1, 1, 0], [0.1, 0.9, 0.4, 0.7], threshold=0.5)
    assert metrics.true_positive == 1
    assert metrics.false_positive == 1
    assert metrics.false_negative == 1
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)

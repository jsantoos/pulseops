from datetime import datetime, timedelta

import pytest

from oie_core.evaluation import evaluate_probabilities, temporal_split
from oie_core.features import cancellation_features
from oie_core.operational_models import Appointment, AppointmentStatus, IdleSlot
from oie_core.prediction import BayesianCancellationBaseline
from oie_core.slot_recovery import rank_slot_recovery


def make_appointment(index: int, exam_type: str, status: AppointmentStatus) -> Appointment:
    scheduled = datetime(2026, 8, 1) + timedelta(days=index, hours=10)
    return Appointment(
        appointment_id=f"a{index}",
        equipment_id="rm-01",
        exam_type=exam_type,
        scheduled_start=scheduled,
        scheduled_duration_minutes=60,
        status=status,
        expected_revenue=1000.0,
        created_at=scheduled - timedelta(days=5),
    )


def test_features_are_leakage_safe_and_reproducible() -> None:
    appointment = make_appointment(1, "MRI_KNEE", AppointmentStatus.CANCELLED)
    features = cancellation_features(appointment)
    assert features.exam_type == "MRI_KNEE"
    assert features.lead_time_days == 5.0
    assert not hasattr(features, "status")


def test_temporal_split_keeps_future_in_validation() -> None:
    rows = [
        (cancellation_features(make_appointment(i, "MRI", AppointmentStatus.COMPLETED)), i % 2)
        for i in range(10)
    ]
    train, validation = temporal_split(list(reversed(rows)), validation_fraction=0.2)
    assert len(train) == 8
    assert len(validation) == 2
    assert max(r[0].scheduled_at for r in train) < min(r[0].scheduled_at for r in validation)


def test_bayesian_baseline_smooths_sparse_exam_types() -> None:
    appointments = [
        make_appointment(0, "MRI_A", AppointmentStatus.CANCELLED),
        make_appointment(1, "MRI_A", AppointmentStatus.COMPLETED),
        make_appointment(2, "MRI_B", AppointmentStatus.COMPLETED),
        make_appointment(3, "MRI_B", AppointmentStatus.COMPLETED),
    ]
    rows = [
        (cancellation_features(item), int(item.status == AppointmentStatus.CANCELLED))
        for item in appointments
    ]
    model = BayesianCancellationBaseline(prior_strength=2.0)
    model.fit(rows)
    prediction_a = model.predict_one(cancellation_features(appointments[0]))
    prediction_unseen = model.predict_one(
        cancellation_features(make_appointment(4, "MRI_NEW", AppointmentStatus.SCHEDULED))
    )
    assert 0 < prediction_a.probability < 1
    assert prediction_unseen.probability == pytest.approx(0.25)
    assert prediction_unseen.evidence_count == 0


def test_probabilistic_metrics_are_finite_and_correct_for_brier() -> None:
    metrics = evaluate_probabilities([0, 1], [0.2, 0.8])
    assert metrics.brier_score == pytest.approx(0.04)
    assert metrics.sample_size == 2
    assert 0 <= metrics.calibration_error <= 1


def test_slot_recovery_prioritizes_expected_revenue() -> None:
    base = datetime(2026, 8, 20, 8)
    slots = [
        IdleSlot("rm-01", base, base + timedelta(minutes=30), 30, 900.0, "gap"),
        IdleSlot("rm-01", base, base + timedelta(minutes=60), 60, 2400.0, "gap"),
    ]
    ranked = rank_slot_recovery(slots, recovery_probability=0.5)
    assert ranked[0].slot.estimated_revenue == 2400.0
    assert ranked[0].expected_recovered_revenue == 1200.0

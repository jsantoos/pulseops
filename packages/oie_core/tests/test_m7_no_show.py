from datetime import datetime, timedelta

from oie_core.no_show import score_future_appointments, train_no_show_model
from oie_core.operational_models import Appointment, AppointmentStatus, AvailabilityWindow, Equipment
from oie_core.portfolio import analyze_operations


def _appointment(index: int, status: AppointmentStatus) -> Appointment:
    scheduled = datetime(2026, 1, 1) + timedelta(days=index)
    lead = 3 if index % 4 else 25
    return Appointment(
        appointment_id=f"a-{index}",
        equipment_id="rm-01",
        exam_type="MRI" if index % 2 else "CT",
        scheduled_start=scheduled,
        scheduled_duration_minutes=60,
        status=status,
        expected_revenue=2000,
        created_at=scheduled - timedelta(days=lead),
    )


def test_no_show_model_produces_probabilities_for_future_appointments() -> None:
    history = [
        _appointment(i, AppointmentStatus.NO_SHOW if i % 5 == 0 else AppointmentStatus.COMPLETED)
        for i in range(80)
    ]
    future = [_appointment(100 + i, AppointmentStatus.CONFIRMED) for i in range(4)]
    model = train_no_show_model(history, min_labeled_rows=40)
    predictions = score_future_appointments(model, future)
    assert len(predictions) == 4
    assert all(0 <= item.probability <= 1 for item in predictions)
    assert model.report.training_rows > model.report.validation_rows


def test_zero_financial_capacity_is_not_published() -> None:
    equipment = [Equipment("rm-01", "RM-01", "MRI", "u1")]
    availability = [
        AvailabilityWindow(
            "rm-01", datetime(2026, 1, 1, 8), datetime(2026, 1, 1, 18)
        )
    ]
    opportunities = analyze_operations(
        equipment=equipment,
        availability=availability,
        appointments=[],
        executions=[],
    )
    assert opportunities == []


def test_no_show_action_policy_combines_risk_and_economics() -> None:
    from oie_core.no_show_actions import NoShowActionType, recommend_no_show_action

    low_value = recommend_no_show_action(
        probability=0.80, expected_net_value=20.0, expected_revenue=100.0
    )
    assert low_value.action_type is NoShowActionType.NO_ACTION

    moderate = recommend_no_show_action(
        probability=0.42, expected_net_value=300.0, expected_revenue=1200.0
    )
    assert moderate.action_type is NoShowActionType.REQUEST_CONFIRMATION

    economically_escalated = recommend_no_show_action(
        probability=0.42, expected_net_value=1200.0, expected_revenue=5000.0
    )
    assert economically_escalated.action_type is NoShowActionType.ACTIVE_CONFIRMATION


def test_no_show_prediction_explanation_uses_model_features() -> None:
    history = [
        _appointment(i, AppointmentStatus.NO_SHOW if i % 5 == 0 else AppointmentStatus.COMPLETED)
        for i in range(80)
    ]
    model = train_no_show_model(history, min_labeled_rows=40)
    prediction = model.predict(_appointment(101, AppointmentStatus.CONFIRMED))
    explanation = prediction.evidence["explanation"]
    assert isinstance(explanation, dict)
    assert explanation["method"] in {
        "local_logistic_contribution",
        "empirical_exam_type_rate",
    }
    factors = explanation["factors"]
    assert isinstance(factors, list)
    assert factors
    assert prediction.recommended_action_type in {
        "no_action",
        "send_reminder",
        "request_confirmation",
        "active_confirmation",
    }

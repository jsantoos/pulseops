from oie_core import EquipmentSnapshot, Severity, analyze_capacity


def test_analyze_capacity_detects_and_ranks_opportunity() -> None:
    snapshots = [
        EquipmentSnapshot(
            equipment_id="rm-02",
            equipment_name="RM-02",
            equipment_type="MRI",
            available_minutes=600,
            booked_minutes=480,
            realized_minutes=360,
            gross_revenue=36_000.0,
        ),
        EquipmentSnapshot(
            equipment_id="ct-01",
            equipment_name="CT-01",
            equipment_type="CT",
            available_minutes=600,
            booked_minutes=560,
            realized_minutes=510,
            gross_revenue=25_500.0,
        ),
    ]

    opportunities = analyze_capacity(snapshots, target_utilization=0.80)

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity.title == "RM-02 below target utilization"
    assert opportunity.severity is Severity.HIGH
    assert opportunity.estimated_gain == 12_000.0
    assert opportunity.evidence["recoverable_minutes"] == 120
    assert 0.0 <= opportunity.score <= 100.0


def test_analyze_capacity_rejects_invalid_target() -> None:
    try:
        analyze_capacity([], target_utilization=1.1)
    except ValueError as exc:
        assert "target_utilization" in str(exc)
    else:
        raise AssertionError("expected ValueError")

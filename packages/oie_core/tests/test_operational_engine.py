from datetime import datetime

from oie_core import (
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    Equipment,
    ExamExecution,
    analyze_operations,
    build_equipment_snapshots,
    detect_idle_slots,
)


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 20, hour, minute)


def test_build_equipment_snapshots_from_granular_data() -> None:
    equipment = [Equipment("rm-02", "RM-02", "MRI", "unit-1")]
    availability = [AvailabilityWindow("rm-02", dt(8), dt(18))]
    appointments = [
        Appointment("a1", "rm-02", "MRI_KNEE", dt(8), 60, AppointmentStatus.COMPLETED, 1200),
        Appointment("a2", "rm-02", "MRI_BRAIN", dt(9), 60, AppointmentStatus.CANCELLED, 1800),
        Appointment("a3", "rm-02", "MRI_SPINE", dt(10), 90, AppointmentStatus.CONFIRMED, 2000),
    ]
    executions = [ExamExecution("a1", dt(8, 5), dt(8, 55), 1200)]

    snapshots = build_equipment_snapshots(
        equipment=equipment,
        availability=availability,
        appointments=appointments,
        executions=executions,
    )

    assert len(snapshots) == 1
    assert snapshots[0].available_minutes == 600
    assert snapshots[0].booked_minutes == 150
    assert snapshots[0].realized_minutes == 50
    assert snapshots[0].gross_revenue == 1200


def test_detect_idle_slots_merges_overlaps_and_ignores_cancelled() -> None:
    availability = [AvailabilityWindow("rm-02", dt(8), dt(12))]
    appointments = [
        Appointment("a1", "rm-02", "MRI", dt(8), 60, AppointmentStatus.CONFIRMED, 1000),
        Appointment("a2", "rm-02", "MRI", dt(9), 60, AppointmentStatus.CANCELLED, 1000),
        Appointment("a3", "rm-02", "MRI", dt(10), 60, AppointmentStatus.CONFIRMED, 1000),
    ]

    slots = detect_idle_slots(
        equipment_id="rm-02",
        availability=availability,
        appointments=appointments,
        revenue_per_minute=20.0,
    )

    assert [(slot.starts_at.hour, slot.ends_at.hour) for slot in slots] == [(9, 10), (11, 12)]
    assert sum(slot.estimated_revenue for slot in slots) == 2400.0


def test_analyze_operations_produces_capacity_and_cancellation_opportunities() -> None:
    equipment = [Equipment("rm-02", "RM-02", "MRI", "unit-1")]
    availability = [AvailabilityWindow("rm-02", dt(8), dt(18))]
    appointments = [
        Appointment("a1", "rm-02", "MRI", dt(8), 60, AppointmentStatus.COMPLETED, 2000),
        Appointment("a2", "rm-02", "MRI", dt(9), 60, AppointmentStatus.CANCELLED, 3000),
        Appointment("a3", "rm-02", "MRI", dt(10), 60, AppointmentStatus.NO_SHOW, 3000),
        Appointment("a4", "rm-02", "MRI", dt(11), 60, AppointmentStatus.CONFIRMED, 2000),
        Appointment("a5", "rm-02", "MRI", dt(12), 60, AppointmentStatus.CONFIRMED, 2000),
    ]
    executions = [ExamExecution("a1", dt(8), dt(9), 2000)]

    opportunities = analyze_operations(
        equipment=equipment,
        availability=availability,
        appointments=appointments,
        executions=executions,
    )

    assert {item.category for item in opportunities} == {"capacity", "cancellation"}
    cancellation = next(item for item in opportunities if item.category == "cancellation")
    assert cancellation.estimated_gain == 6000.0
    assert cancellation.evidence["loss_rate"] == 0.4

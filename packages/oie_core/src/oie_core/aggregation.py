"""Aggregation from granular operations into deterministic capacity snapshots."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import EquipmentSnapshot
from .operational_models import (
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    Equipment,
    ExamExecution,
)


def build_equipment_snapshots(
    *,
    equipment: Iterable[Equipment],
    availability: Iterable[AvailabilityWindow],
    appointments: Iterable[Appointment],
    executions: Iterable[ExamExecution],
) -> list[EquipmentSnapshot]:
    """Build auditable aggregate capacity facts from granular operational data."""

    equipment_by_id = {item.equipment_id: item for item in equipment}
    available_minutes: dict[str, int] = defaultdict(int)
    booked_minutes: dict[str, int] = defaultdict(int)
    realized_minutes: dict[str, int] = defaultdict(int)
    gross_revenue: dict[str, float] = defaultdict(float)

    for window in availability:
        if window.equipment_id not in equipment_by_id:
            raise ValueError(f"unknown equipment_id in availability: {window.equipment_id}")
        if window.ends_at <= window.starts_at:
            raise ValueError("availability window must end after it starts")
        available_minutes[window.equipment_id] += window.duration_minutes

    appointment_by_id = {item.appointment_id: item for item in appointments}
    for appointment in appointment_by_id.values():
        if appointment.equipment_id not in equipment_by_id:
            raise ValueError(f"unknown equipment_id in appointment: {appointment.equipment_id}")
        if appointment.scheduled_duration_minutes <= 0:
            raise ValueError("scheduled_duration_minutes must be positive")
        if appointment.status not in {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}:
            booked_minutes[appointment.equipment_id] += appointment.scheduled_duration_minutes

    seen_executions: set[str] = set()
    for execution in executions:
        if execution.appointment_id in seen_executions:
            raise ValueError(f"duplicate execution for appointment: {execution.appointment_id}")
        seen_executions.add(execution.appointment_id)
        appointment = appointment_by_id.get(execution.appointment_id)
        if appointment is None:
            raise ValueError(f"execution references unknown appointment: {execution.appointment_id}")
        if execution.actual_end <= execution.actual_start:
            raise ValueError("execution actual_end must be after actual_start")
        realized_minutes[appointment.equipment_id] += execution.duration_minutes
        gross_revenue[appointment.equipment_id] += max(execution.realized_revenue, 0.0)

    snapshots: list[EquipmentSnapshot] = []
    for equipment_id, item in equipment_by_id.items():
        snapshots.append(
            EquipmentSnapshot(
                equipment_id=equipment_id,
                equipment_name=item.name,
                equipment_type=item.equipment_type,
                available_minutes=available_minutes[equipment_id],
                booked_minutes=booked_minutes[equipment_id],
                realized_minutes=realized_minutes[equipment_id],
                gross_revenue=round(gross_revenue[equipment_id], 2),
            )
        )

    return sorted(snapshots, key=lambda item: item.equipment_id)

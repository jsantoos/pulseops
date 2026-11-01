"""Deterministic detection of recoverable idle capacity."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from .operational_models import (
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    IdleSlot,
)


def detect_idle_slots(
    *,
    equipment_id: str,
    availability: Iterable[AvailabilityWindow],
    appointments: Iterable[Appointment],
    revenue_per_minute: float,
    minimum_slot_minutes: int = 15,
) -> list[IdleSlot]:
    """Return free windows within equipment availability.

    Cancelled and no-show appointments do not occupy future/recoverable capacity.
    Overlapping scheduled appointments are merged before gaps are calculated.
    """

    if minimum_slot_minutes <= 0:
        raise ValueError("minimum_slot_minutes must be positive")

    windows = sorted(
        (w for w in availability if w.equipment_id == equipment_id),
        key=lambda w: w.starts_at,
    )
    active = sorted(
        (
            a
            for a in appointments
            if a.equipment_id == equipment_id
            and a.status not in {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
        ),
        key=lambda a: a.scheduled_start,
    )

    slots: list[IdleSlot] = []
    for window in windows:
        if window.ends_at <= window.starts_at:
            raise ValueError("availability window must end after it starts")

        intervals: list[tuple[datetime, datetime]] = []
        for appointment in active:
            start = max(appointment.scheduled_start, window.starts_at)
            end = min(appointment.scheduled_end, window.ends_at)
            if start < end:
                intervals.append((start, end))

        merged: list[list[datetime]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            elif end > merged[-1][1]:
                merged[-1][1] = end

        cursor = window.starts_at
        for start, end in merged:
            if start > cursor:
                _append_slot(
                    slots,
                    equipment_id,
                    cursor,
                    start,
                    revenue_per_minute,
                    minimum_slot_minutes,
                )
            cursor = max(cursor, end)
        if cursor < window.ends_at:
            _append_slot(
                slots,
                equipment_id,
                cursor,
                window.ends_at,
                revenue_per_minute,
                minimum_slot_minutes,
            )

    return slots


def _append_slot(
    slots: list[IdleSlot],
    equipment_id: str,
    start: datetime,
    end: datetime,
    revenue_per_minute: float,
    minimum_slot_minutes: int,
) -> None:
    duration = round((end - start).total_seconds() / 60.0)
    if duration < minimum_slot_minutes:
        return
    slots.append(
        IdleSlot(
            equipment_id=equipment_id,
            starts_at=start,
            ends_at=end,
            duration_minutes=duration,
            estimated_revenue=round(max(revenue_per_minute, 0.0) * duration, 2),
            source="schedule_gap",
        )
    )

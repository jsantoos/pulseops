"""Cancellation and no-show analytics for OIE M1."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .operational_models import Appointment, AppointmentStatus


@dataclass(frozen=True, slots=True)
class CancellationSummary:
    equipment_id: str
    total_appointments: int
    cancelled: int
    no_shows: int
    lost_revenue: float

    @property
    def loss_rate(self) -> float:
        if self.total_appointments <= 0:
            return 0.0
        return (self.cancelled + self.no_shows) / self.total_appointments


def summarize_cancellations(
    appointments: Iterable[Appointment],
) -> list[CancellationSummary]:
    total: dict[str, int] = defaultdict(int)
    cancelled: dict[str, int] = defaultdict(int)
    no_shows: dict[str, int] = defaultdict(int)
    lost_revenue: dict[str, float] = defaultdict(float)

    for appointment in appointments:
        total[appointment.equipment_id] += 1
        if appointment.status is AppointmentStatus.CANCELLED:
            cancelled[appointment.equipment_id] += 1
            lost_revenue[appointment.equipment_id] += max(appointment.expected_revenue, 0.0)
        elif appointment.status is AppointmentStatus.NO_SHOW:
            no_shows[appointment.equipment_id] += 1
            lost_revenue[appointment.equipment_id] += max(appointment.expected_revenue, 0.0)

    return [
        CancellationSummary(
            equipment_id=equipment_id,
            total_appointments=total[equipment_id],
            cancelled=cancelled[equipment_id],
            no_shows=no_shows[equipment_id],
            lost_revenue=round(lost_revenue[equipment_id], 2),
        )
        for equipment_id in sorted(total)
    ]

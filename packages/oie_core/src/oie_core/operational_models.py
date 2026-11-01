"""Granular operational domain models for OIE.

These models are framework-independent and intentionally avoid PHI/PII fields in
M1. The capacity engine only needs operational facts, not patient identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class Equipment:
    equipment_id: str
    name: str
    equipment_type: str
    unit_id: str


@dataclass(frozen=True, slots=True)
class Appointment:
    appointment_id: str
    equipment_id: str
    exam_type: str
    scheduled_start: datetime
    scheduled_duration_minutes: int
    status: AppointmentStatus
    expected_revenue: float
    created_at: datetime | None = None
    cancelled_at: datetime | None = None

    @property
    def scheduled_end(self) -> datetime:
        from datetime import timedelta

        return self.scheduled_start + timedelta(minutes=self.scheduled_duration_minutes)


@dataclass(frozen=True, slots=True)
class ExamExecution:
    appointment_id: str
    actual_start: datetime
    actual_end: datetime
    realized_revenue: float

    @property
    def duration_minutes(self) -> int:
        seconds = (self.actual_end - self.actual_start).total_seconds()
        return max(round(seconds / 60.0), 0)


@dataclass(frozen=True, slots=True)
class AvailabilityWindow:
    equipment_id: str
    starts_at: datetime
    ends_at: datetime

    @property
    def duration_minutes(self) -> int:
        seconds = (self.ends_at - self.starts_at).total_seconds()
        return max(round(seconds / 60.0), 0)


@dataclass(frozen=True, slots=True)
class IdleSlot:
    equipment_id: str
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int
    estimated_revenue: float
    source: str

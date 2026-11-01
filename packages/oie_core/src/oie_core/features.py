"""Versioned predictive features for operational risk models.

M2 deliberately uses only operational, non-identifying features. Feature values
are derived from facts available before the scheduled appointment start to
avoid target leakage.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .operational_models import Appointment

FEATURE_SET_VERSION = "cancellation-v1"


@dataclass(frozen=True, slots=True)
class CancellationFeatures:
    appointment_id: str
    equipment_id: str
    exam_type: str
    hour_of_day: int
    day_of_week: int
    lead_time_days: float
    expected_revenue: float
    scheduled_at: datetime


def cancellation_features(appointment: Appointment) -> CancellationFeatures:
    """Build leakage-safe features known before the appointment occurs."""
    lead_time_days = 0.0
    if appointment.created_at is not None:
        seconds = (appointment.scheduled_start - appointment.created_at).total_seconds()
        lead_time_days = max(seconds / 86400.0, 0.0)
    return CancellationFeatures(
        appointment_id=appointment.appointment_id,
        equipment_id=appointment.equipment_id,
        exam_type=appointment.exam_type,
        hour_of_day=appointment.scheduled_start.hour,
        day_of_week=appointment.scheduled_start.weekday(),
        lead_time_days=lead_time_days,
        expected_revenue=max(appointment.expected_revenue, 0.0),
        scheduled_at=appointment.scheduled_start,
    )

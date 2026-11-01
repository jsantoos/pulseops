from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from oie_core.operational_models import Appointment, AppointmentStatus, AvailabilityWindow, Equipment, ExamExecution


@dataclass(frozen=True, slots=True)
class OperationalDataset:
    equipment: tuple[Equipment, ...]
    availability: tuple[AvailabilityWindow, ...]
    appointments: tuple[Appointment, ...]
    executions: tuple[ExamExecution, ...]


_REQUIRED_KEYS = {"equipment", "availability", "appointments", "executions"}


def parse_operational_json(raw: str) -> OperationalDataset:
    payload = json.loads(raw)
    missing = _REQUIRED_KEYS - payload.keys()
    if missing:
        raise ValueError(f"missing dataset sections: {sorted(missing)}")

    equipment = tuple(Equipment(**row) for row in payload["equipment"])
    availability = tuple(
        AvailabilityWindow(
            equipment_id=row["equipment_id"],
            starts_at=_dt(row["starts_at"]),
            ends_at=_dt(row["ends_at"]),
        )
        for row in payload["availability"]
    )
    appointments = tuple(
        Appointment(
            appointment_id=row["appointment_id"],
            equipment_id=row["equipment_id"],
            exam_type=row["exam_type"],
            scheduled_start=_dt(row["scheduled_start"]),
            scheduled_duration_minutes=int(row["scheduled_duration_minutes"]),
            status=AppointmentStatus(row["status"]),
            expected_revenue=float(row["expected_revenue"]),
            created_at=_optional_dt(row.get("created_at")),
            cancelled_at=_optional_dt(row.get("cancelled_at")),
        )
        for row in payload["appointments"]
    )
    executions = tuple(
        ExamExecution(
            appointment_id=row["appointment_id"],
            actual_start=_dt(row["actual_start"]),
            actual_end=_dt(row["actual_end"]),
            realized_revenue=float(row["realized_revenue"]),
        )
        for row in payload["executions"]
    )
    return OperationalDataset(equipment, availability, appointments, executions)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _optional_dt(value: str | None) -> datetime | None:
    return None if value is None else _dt(value)

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from oie_core import (
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    Equipment,
    ExamExecution,
    analyze_operations,
)

ROOT = Path(__file__).resolve().parents[1]


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def main() -> None:
    payload = json.loads((ROOT / "datasets/sample/operations.json").read_text())
    equipment = [Equipment(**item) for item in payload["equipment"]]
    availability = [
        AvailabilityWindow(
            equipment_id=item["equipment_id"],
            starts_at=parse_dt(item["starts_at"]),
            ends_at=parse_dt(item["ends_at"]),
        )
        for item in payload["availability"]
    ]
    appointments = [
        Appointment(
            appointment_id=item["appointment_id"],
            equipment_id=item["equipment_id"],
            exam_type=item["exam_type"],
            scheduled_start=parse_dt(item["scheduled_start"]),
            scheduled_duration_minutes=item["scheduled_duration_minutes"],
            status=AppointmentStatus(item["status"]),
            expected_revenue=float(item["expected_revenue"]),
        )
        for item in payload["appointments"]
    ]
    executions = [
        ExamExecution(
            appointment_id=item["appointment_id"],
            actual_start=parse_dt(item["actual_start"]),
            actual_end=parse_dt(item["actual_end"]),
            realized_revenue=float(item["realized_revenue"]),
        )
        for item in payload["executions"]
    ]

    opportunities = analyze_operations(
        equipment=equipment,
        availability=availability,
        appointments=appointments,
        executions=executions,
    )
    print(json.dumps([asdict(item) for item in opportunities], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

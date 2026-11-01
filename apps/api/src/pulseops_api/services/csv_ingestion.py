from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable

from oie_core.operational_models import (
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    Equipment,
    ExamExecution,
)

from pulseops_api.services.ingestion import OperationalDataset


@dataclass(frozen=True, slots=True)
class DataIssue:
    file: str
    row: int
    field: str | None
    message: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    rows_received: int
    rows_valid: int
    rows_rejected: int
    issues: tuple[DataIssue, ...]

    @property
    def status(self) -> str:
        if self.rows_rejected:
            return "accepted_with_errors"
        if self.issues:
            return "accepted_with_warnings"
        return "accepted"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "rows_received": self.rows_received,
            "rows_valid": self.rows_valid,
            "rows_rejected": self.rows_rejected,
            "issues": [asdict(issue) for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class CsvBundleResult:
    dataset: OperationalDataset
    report: DataQualityReport

    def canonical_json(self) -> str:
        return json.dumps(
            {
                "equipment": [
                    {
                        "equipment_id": x.equipment_id,
                        "name": x.name,
                        "equipment_type": x.equipment_type,
                        "unit_id": x.unit_id,
                    }
                    for x in self.dataset.equipment
                ],
                "availability": [
                    {
                        "equipment_id": x.equipment_id,
                        "starts_at": x.starts_at.isoformat(),
                        "ends_at": x.ends_at.isoformat(),
                    }
                    for x in self.dataset.availability
                ],
                "appointments": [
                    {
                        "appointment_id": x.appointment_id,
                        "equipment_id": x.equipment_id,
                        "exam_type": x.exam_type,
                        "scheduled_start": x.scheduled_start.isoformat(),
                        "scheduled_duration_minutes": x.scheduled_duration_minutes,
                        "status": x.status.value,
                        "expected_revenue": x.expected_revenue,
                        "created_at": x.created_at.isoformat() if x.created_at else None,
                        "cancelled_at": x.cancelled_at.isoformat() if x.cancelled_at else None,
                    }
                    for x in self.dataset.appointments
                ],
                "executions": [
                    {
                        "appointment_id": x.appointment_id,
                        "actual_start": x.actual_start.isoformat(),
                        "actual_end": x.actual_end.isoformat(),
                        "realized_revenue": x.realized_revenue,
                    }
                    for x in self.dataset.executions
                ],
            },
            separators=(",", ":"),
        )


def parse_csv_bundle(
    *,
    equipment_csv: bytes,
    availability_csv: bytes,
    appointments_csv: bytes,
    executions_csv: bytes,
) -> CsvBundleResult:
    issues: list[DataIssue] = []
    received = valid = rejected = 0

    equipment, stats = _parse_equipment(equipment_csv, issues)
    received += stats[0]; valid += stats[1]; rejected += stats[2]
    availability, stats = _parse_availability(availability_csv, issues)
    received += stats[0]; valid += stats[1]; rejected += stats[2]
    appointments, stats = _parse_appointments(appointments_csv, issues)
    received += stats[0]; valid += stats[1]; rejected += stats[2]
    executions, stats = _parse_executions(executions_csv, issues)
    received += stats[0]; valid += stats[1]; rejected += stats[2]

    equipment_ids = {x.equipment_id for x in equipment}
    appointment_ids = {x.appointment_id for x in appointments}
    for item in availability:
        if item.equipment_id not in equipment_ids:
            issues.append(DataIssue("availability.csv", 0, "equipment_id", f"unknown equipment_id: {item.equipment_id}"))
    for item in appointments:
        if item.equipment_id not in equipment_ids:
            issues.append(DataIssue("appointments.csv", 0, "equipment_id", f"unknown equipment_id: {item.equipment_id}"))
    for item in executions:
        if item.appointment_id not in appointment_ids:
            issues.append(DataIssue("executions.csv", 0, "appointment_id", f"unknown appointment_id: {item.appointment_id}"))

    if any(issue.severity == "error" and issue.row == 0 for issue in issues):
        raise ValueError("cross-file references are invalid")

    return CsvBundleResult(
        dataset=OperationalDataset(tuple(equipment), tuple(availability), tuple(appointments), tuple(executions)),
        report=DataQualityReport(received, valid, rejected, tuple(issues)),
    )


def _rows(raw: bytes, file_name: str) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{file_name}: file must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError(f"{file_name}: missing CSV header")
    return list(reader)


def _require(row: dict[str, str], required: Iterable[str], file_name: str) -> None:
    missing = [name for name in required if not (row.get(name) or "").strip()]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))


def _opt_dt(value: str | None) -> datetime | None:
    return None if not value or not value.strip() else _dt(value)


def _parse_equipment(raw: bytes, issues: list[DataIssue]):
    data=[]; rows=_rows(raw,"equipment.csv"); rejected=0
    for number,row in enumerate(rows, start=2):
        try:
            _require(row,("equipment_id","name","equipment_type","unit_id"),"equipment.csv")
            data.append(Equipment(*(row[k].strip() for k in ("equipment_id","name","equipment_type","unit_id"))))
        except Exception as exc:
            rejected += 1; issues.append(DataIssue("equipment.csv",number,None,str(exc)))
    return data,(len(rows),len(data),rejected)


def _parse_availability(raw: bytes, issues: list[DataIssue]):
    data=[]; rows=_rows(raw,"availability.csv"); rejected=0
    for number,row in enumerate(rows, start=2):
        try:
            _require(row,("equipment_id","starts_at","ends_at"),"availability.csv")
            item=AvailabilityWindow(row["equipment_id"].strip(),_dt(row["starts_at"]),_dt(row["ends_at"]))
            if item.ends_at <= item.starts_at: raise ValueError("ends_at must be later than starts_at")
            data.append(item)
        except Exception as exc:
            rejected += 1; issues.append(DataIssue("availability.csv",number,None,str(exc)))
    return data,(len(rows),len(data),rejected)


def _parse_appointments(raw: bytes, issues: list[DataIssue]):
    data=[]; rows=_rows(raw,"appointments.csv"); rejected=0
    required=("appointment_id","equipment_id","exam_type","scheduled_start","scheduled_duration_minutes","status","expected_revenue")
    for number,row in enumerate(rows, start=2):
        try:
            _require(row,required,"appointments.csv")
            duration=int(row["scheduled_duration_minutes"])
            revenue=float(row["expected_revenue"])
            if duration <= 0: raise ValueError("scheduled_duration_minutes must be > 0")
            if revenue < 0: raise ValueError("expected_revenue must be >= 0")
            data.append(Appointment(row["appointment_id"].strip(),row["equipment_id"].strip(),row["exam_type"].strip(),_dt(row["scheduled_start"]),duration,AppointmentStatus(row["status"].strip()),revenue,_opt_dt(row.get("created_at")),_opt_dt(row.get("cancelled_at"))))
        except Exception as exc:
            rejected += 1; issues.append(DataIssue("appointments.csv",number,None,str(exc)))
    return data,(len(rows),len(data),rejected)


def _parse_executions(raw: bytes, issues: list[DataIssue]):
    data=[]; rows=_rows(raw,"executions.csv"); rejected=0
    required=("appointment_id","actual_start","actual_end","realized_revenue")
    for number,row in enumerate(rows, start=2):
        try:
            _require(row,required,"executions.csv")
            item=ExamExecution(row["appointment_id"].strip(),_dt(row["actual_start"]),_dt(row["actual_end"]),float(row["realized_revenue"]))
            if item.actual_end <= item.actual_start: raise ValueError("actual_end must be later than actual_start")
            if item.realized_revenue < 0: raise ValueError("realized_revenue must be >= 0")
            data.append(item)
        except Exception as exc:
            rejected += 1; issues.append(DataIssue("executions.csv",number,None,str(exc)))
    return data,(len(rows),len(data),rejected)

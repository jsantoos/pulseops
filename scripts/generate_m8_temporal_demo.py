from __future__ import annotations

import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "datasets" / "no-show-demo"
PERIOD_2 = ROOT / "datasets" / "no-show-demo-period-2"
PERIOD_3 = ROOT / "datasets" / "no-show-demo-period-3"

FUTURE_DAYS = 7


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def execution_for(
    appointment: dict[str, str],
) -> dict[str, str]:
    scheduled = datetime.fromisoformat(
        appointment["scheduled_start"],
    )

    actual_start = scheduled + timedelta(minutes=4)

    duration = int(
        appointment["scheduled_duration_minutes"],
    )

    actual_end = actual_start + timedelta(
        minutes=max(duration - 3, 1),
    )

    return {
        "appointment_id": appointment["appointment_id"],
        "actual_start": actual_start.isoformat(),
        "actual_end": actual_end.isoformat(),
        "realized_revenue": appointment["expected_revenue"],
    }


def refresh_future_appointments(
    appointments: list[dict[str, str]],
    *,
    period_offset_days: int,
) -> int:
    """
    Move only confirmed appointments into a future inference window.

    Historical completed/no_show/cancelled appointments remain untouched.
    This keeps the temporal OIE demo stable while ensuring the ML pipeline
    always has future appointments to score.
    """

    confirmed = [
        row
        for row in appointments
        if row["status"] == "confirmed"
    ]

    confirmed.sort(
        key=lambda row: (
            row["scheduled_start"],
            row["appointment_id"],
        ),
    )

    if not confirmed:
        return 0

    # Start tomorrow so every generated appointment is safely in the future.
    base_date = (
        datetime.now()
        .replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        + timedelta(days=1 + period_offset_days)
    )

    for index, appointment in enumerate(confirmed):
        day_offset = index % FUTURE_DAYS

        # Keep four practical appointment slots per day.
        slot = index % 4
        hour = 8 + (slot * 2)

        scheduled = (
            base_date
            + timedelta(days=day_offset)
        ).replace(
            hour=hour,
            minute=0,
            second=0,
            microsecond=0,
        )

        appointment["scheduled_start"] = (
            scheduled.isoformat()
        )

        # Preserve a realistic lead time pattern.
        lead_days = (index % 4) * 7 + 3

        created_at = scheduled - timedelta(
            days=lead_days,
        )

        appointment["created_at"] = (
            created_at.isoformat()
        )

        appointment["cancelled_at"] = ""

    return len(confirmed)


def generate_period(
    source_directory: Path,
    destination: Path,
    *,
    rm02_recover_no_shows: int,
    rm01_create_no_shows: int,
    future_period_offset_days: int,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(
        source_directory,
        destination,
    )

    appointments_path = (
        destination / "appointments.csv"
    )

    executions_path = (
        destination / "executions.csv"
    )

    appointments = read_csv(
        appointments_path,
    )

    executions = read_csv(
        executions_path,
    )

    execution_by_id = {
        row["appointment_id"]: row
        for row in executions
    }

    rm02_candidates = sorted(
        (
            row
            for row in appointments
            if row["equipment_id"] == "rm-02"
            and row["status"] == "no_show"
            and row["scheduled_start"]
            < "2026-07-27T00:00:00"
        ),
        key=lambda row: row["scheduled_start"],
    )

    recovered = 0

    for appointment in rm02_candidates:
        if recovered >= rm02_recover_no_shows:
            break

        appointment["status"] = "completed"
        appointment["cancelled_at"] = ""

        appointment_id = appointment[
            "appointment_id"
        ]

        if appointment_id not in execution_by_id:
            execution = execution_for(
                appointment,
            )

            executions.append(execution)

            execution_by_id[
                appointment_id
            ] = execution

        recovered += 1

    rm01_candidates = sorted(
        (
            row
            for row in appointments
            if row["equipment_id"] == "rm-01"
            and row["status"] == "completed"
            and row["appointment_id"]
            in execution_by_id
        ),
        key=lambda row: row["scheduled_start"],
        reverse=True,
    )

    worsened = 0

    for appointment in rm01_candidates:
        if worsened >= rm01_create_no_shows:
            break

        appointment["status"] = "no_show"
        appointment["cancelled_at"] = ""

        appointment_id = appointment[
            "appointment_id"
        ]

        executions = [
            row
            for row in executions
            if row["appointment_id"]
            != appointment_id
        ]

        execution_by_id.pop(
            appointment_id,
            None,
        )

        worsened += 1

    future_appointments = refresh_future_appointments(
        appointments,
        period_offset_days=future_period_offset_days,
    )

    write_csv(
        appointments_path,
        appointments,
        [
            "appointment_id",
            "equipment_id",
            "exam_type",
            "scheduled_start",
            "scheduled_duration_minutes",
            "status",
            "expected_revenue",
            "created_at",
            "cancelled_at",
        ],
    )

    write_csv(
        executions_path,
        executions,
        [
            "appointment_id",
            "actual_start",
            "actual_end",
            "realized_revenue",
        ],
    )

    print(
        destination.name,
        {
            "rm02_recovered": recovered,
            "rm01_new_no_shows": worsened,
            "executions": len(executions),
            "future_appointments": future_appointments,
        },
    )


def main() -> None:
    generate_period(
        SOURCE,
        PERIOD_2,
        rm02_recover_no_shows=20,
        rm01_create_no_shows=5,
        future_period_offset_days=0,
    )

    generate_period(
        PERIOD_2,
        PERIOD_3,
        rm02_recover_no_shows=20,
        rm01_create_no_shows=5,
        future_period_offset_days=7,
    )


if __name__ == "__main__":
    main()
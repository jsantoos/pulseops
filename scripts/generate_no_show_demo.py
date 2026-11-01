#!/usr/bin/env python3
"""Generate deterministic synthetic operational data for M7 demos/tests.

No patient identifiers are generated. The dataset encodes known risk patterns
in temporal/operational features so the ML pipeline can be evaluated safely.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20260820
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "no-show-demo"


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    equipment = [
        ("rm-01", "RM-01", "MRI", "unit-1"),
        ("rm-02", "RM-02", "MRI", "unit-1"),
    ]
    with (OUT / "equipment.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["equipment_id", "name", "equipment_type", "unit_id"])
        w.writerows(equipment)

    start_day = datetime(2026, 5, 1)
    historical_days = 80
    future_days = 7
    with (OUT / "availability.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["equipment_id", "starts_at", "ends_at"])
        for day_offset in range(historical_days + future_days):
            day = start_day + timedelta(days=day_offset)
            for equipment_id, *_ in equipment:
                w.writerow([
                    equipment_id,
                    day.replace(hour=8).isoformat(),
                    day.replace(hour=18).isoformat(),
                ])

    appointments: list[list[object]] = []
    executions: list[list[object]] = []
    appointment_index = 0
    exam_types = ["MRI_KNEE", "MRI_BRAIN", "MRI_SPINE"]
    for day_offset in range(historical_days):
        day = start_day + timedelta(days=day_offset)
        for slot in range(5):
            appointment_index += 1
            hour = 8 + slot * 2
            scheduled = day.replace(hour=hour, minute=0)
            equipment_id = "rm-02" if appointment_index % 3 else "rm-01"
            exam_type = exam_types[appointment_index % len(exam_types)]
            lead_days = rng.randint(1, 35)
            created_at = scheduled - timedelta(days=lead_days)
            expected_revenue = float([1400, 2200, 3000][appointment_index % 3])

            # Synthetic ground truth: long lead times, late afternoon and Monday
            # raise risk. Higher-value exams have slightly lower observed risk.
            logit = -2.8
            logit += 0.075 * lead_days
            logit += 0.9 if hour >= 14 else 0.0
            logit += 0.55 if scheduled.weekday() == 0 else 0.0
            logit += 0.35 if equipment_id == "rm-02" else 0.0
            logit -= 0.25 if expected_revenue >= 3000 else 0.0
            probability = min(max(sigmoid(logit), 0.03), 0.85)
            no_show = rng.random() < probability
            status = "no_show" if no_show else "completed"
            appointment_id = f"hist-{appointment_index:04d}"
            appointments.append([
                appointment_id,
                equipment_id,
                exam_type,
                scheduled.isoformat(),
                60,
                status,
                expected_revenue,
                created_at.isoformat(),
                "",
            ])
            if not no_show:
                actual_start = scheduled + timedelta(minutes=rng.randint(0, 10))
                actual_end = actual_start + timedelta(minutes=rng.randint(48, 62))
                executions.append([
                    appointment_id,
                    actual_start.isoformat(),
                    actual_end.isoformat(),
                    expected_revenue,
                ])

    future_start = start_day + timedelta(days=historical_days)
    for day_offset in range(future_days):
        day = future_start + timedelta(days=day_offset)
        for slot in range(4):
            appointment_index += 1
            hour = 8 + slot * 2
            scheduled = day.replace(hour=hour)
            lead_days = [3, 10, 22, 32][slot]
            equipment_id = "rm-02" if slot % 2 else "rm-01"
            exam_type = exam_types[(slot + day_offset) % len(exam_types)]
            expected_revenue = float([1400, 2200, 3000, 2400][slot])
            appointments.append([
                f"future-{appointment_index:04d}",
                equipment_id,
                exam_type,
                scheduled.isoformat(),
                60,
                "confirmed",
                expected_revenue,
                (scheduled - timedelta(days=lead_days)).isoformat(),
                "",
            ])

    with (OUT / "appointments.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "appointment_id",
            "equipment_id",
            "exam_type",
            "scheduled_start",
            "scheduled_duration_minutes",
            "status",
            "expected_revenue",
            "created_at",
            "cancelled_at",
        ])
        w.writerows(appointments)

    with (OUT / "executions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["appointment_id", "actual_start", "actual_end", "realized_revenue"])
        w.writerows(executions)

    print(f"Generated {len(appointments)} appointments in {OUT}")


if __name__ == "__main__":
    main()

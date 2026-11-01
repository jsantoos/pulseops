#!/usr/bin/env python3
"""Demonstrate OIE M2 temporal evaluation on deterministic synthetic operations."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from oie_core import (
    Appointment,
    AppointmentStatus,
    BayesianCancellationBaseline,
    cancellation_features,
    evaluate_probabilities,
    temporal_split,
)


def main() -> None:
    rng = random.Random(42)
    rows = []
    start = datetime(2026, 1, 1, 9)
    for i in range(120):
        exam_type = "MRI_LONG" if i % 3 == 0 else "MRI_STD"
        # Synthetic ground truth only for engineering evaluation.
        base_risk = 0.28 if exam_type == "MRI_LONG" else 0.12
        target = int(rng.random() < base_risk)
        scheduled = start + timedelta(days=i)
        appointment = Appointment(
            appointment_id=f"syn-{i:04d}",
            equipment_id="rm-01",
            exam_type=exam_type,
            scheduled_start=scheduled,
            scheduled_duration_minutes=60,
            status=AppointmentStatus.CANCELLED if target else AppointmentStatus.COMPLETED,
            expected_revenue=1500.0,
            created_at=scheduled - timedelta(days=7 + i % 10),
        )
        rows.append((cancellation_features(appointment), target))

    train, validation = temporal_split(rows, validation_fraction=0.25)
    model = BayesianCancellationBaseline(prior_strength=10.0)
    model.fit(train)
    probabilities = [model.predict_one(features).probability for features, _ in validation]
    metrics = evaluate_probabilities([target for _, target in validation], probabilities)

    output = {
        "model_version": model.model_version,
        "feature_set_version": "cancellation-v1",
        "split": {"train": len(train), "validation": len(validation), "strategy": "temporal"},
        "metrics": {
            "brier_score": round(metrics.brier_score, 6),
            "log_loss": round(metrics.log_loss, 6),
            "calibration_error": round(metrics.calibration_error, 6),
            "positive_rate": round(metrics.positive_rate, 6),
            "sample_size": metrics.sample_size,
        },
        "warning": "Synthetic-data metrics are engineering checks, not evidence of real-world performance.",
    }
    target = Path("m2-evaluation-output.json")
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

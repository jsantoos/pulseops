from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from oie_core.calibration import PlattCalibrator
from oie_core.decision_curve import build_decision_curve
from oie_core.decision_policy import InterventionEconomics
from oie_core.evaluation import evaluate_probabilities
from oie_core.policy_optimization import DecisionCase, PolicySearchSpace, optimize_policy

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    targets = [0, 0, 0, 1, 1, 1] * 20
    raw = [0.001, 0.001, 0.001, 0.999, 0.999, 0.999] * 20
    before = evaluate_probabilities(targets, raw)
    calibrator = PlattCalibrator(epochs=1500, learning_rate=0.02)
    calibrator.fit(raw, targets)
    calibrated = calibrator.transform(raw)
    after = evaluate_probabilities(targets, calibrated)

    start = datetime(2026, 1, 1, 8)
    cases = [
        DecisionCase(
            occurred_at=start + timedelta(days=i),
            cancellation_probability=0.70 if i % 4 == 0 else 0.08,
            cancelled=i % 4 == 0,
            expected_revenue=1800.0 if i % 4 == 0 else 600.0,
        )
        for i in range(40)
    ]
    economics = InterventionEconomics(intervention_cost=20.0, success_probability=0.5)
    best = optimize_policy(
        cases,
        economics=economics,
        search_space=PolicySearchSpace(max_action_rate=0.30),
    )
    curve = build_decision_curve(
        cases,
        economics=economics,
        thresholds=(0.05, 0.10, 0.20, 0.30, 0.50, 0.80),
    )

    payload = {
        "synthetic_only": True,
        "calibration": {
            "before": {
                "brier_score": before.brier_score,
                "log_loss": before.log_loss,
                "calibration_error": before.calibration_error,
            },
            "after": {
                "brier_score": after.brier_score,
                "log_loss": after.log_loss,
                "calibration_error": after.calibration_error,
            },
            "calibrator_version": calibrator.version,
        },
        "optimized_policy": {
            "min_risk_probability": best.policy.min_risk_probability,
            "min_expected_net_value": best.policy.min_expected_net_value,
            "action_rate": best.action_rate,
            "action_count": best.action_count,
            "recovered_revenue": best.recovered_revenue,
            "intervention_cost": best.intervention_cost,
            "net_value": best.net_value,
        },
        "decision_curve": [
            {
                "risk_threshold": point.risk_threshold,
                "net_value": point.net_value,
                "action_rate": point.action_rate,
                "recovered_revenue": point.recovered_revenue,
            }
            for point in curve
        ],
    }
    output = ROOT / "m4-evaluation-output.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

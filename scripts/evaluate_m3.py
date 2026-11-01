from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oie_core" / "src"))

from oie_core.challengers import LogisticCancellationChallenger
from oie_core.decision_policy import InterventionEconomics, decide_intervention
from oie_core.evaluation import evaluate_probabilities, temporal_split
from oie_core.features import cancellation_features
from oie_core.model_governance import evaluate_promotion
from oie_core.operational_models import Appointment, AppointmentStatus
from oie_core.prediction import BayesianCancellationBaseline


def build_dataset() -> list[tuple]:
    rows = []
    start = datetime(2026, 1, 1, 8)
    for index in range(180):
        scheduled = start + timedelta(days=index, hours=index % 10)
        risky = (index % 5 == 0) or (scheduled.hour >= 16 and index % 3 == 0)
        lead_days = 18 if risky else 4 + index % 4
        status = AppointmentStatus.CANCELLED if risky else AppointmentStatus.COMPLETED
        appointment = Appointment(
            appointment_id=f"eval-{index}",
            equipment_id="rm-01",
            exam_type="MRI_KNEE" if index % 2 else "MRI_SPINE",
            scheduled_start=scheduled,
            scheduled_duration_minutes=60,
            status=status,
            expected_revenue=1200.0 + (index % 4) * 300,
            created_at=scheduled - timedelta(days=lead_days),
        )
        rows.append((cancellation_features(appointment), int(risky)))
    return rows


def main() -> None:
    train, validation = temporal_split(build_dataset(), validation_fraction=0.25)
    champion = BayesianCancellationBaseline(prior_strength=10)
    challenger = LogisticCancellationChallenger(epochs=700)
    champion.fit(train)
    challenger.fit(train)

    y_true = [target for _, target in validation]
    champion_probs = [champion.predict_one(features).probability for features, _ in validation]
    challenger_probs = [challenger.predict_one(features).probability for features, _ in validation]
    champion_metrics = evaluate_probabilities(y_true, champion_probs)
    challenger_metrics = evaluate_probabilities(y_true, challenger_probs)
    promotion = evaluate_promotion(champion_metrics, challenger_metrics)

    sample_features, _ = validation[-1]
    chosen_probability = (
        challenger.predict_one(sample_features).probability
        if promotion.promote
        else champion.predict_one(sample_features).probability
    )
    decision = decide_intervention(
        cancellation_probability=chosen_probability,
        expected_revenue=sample_features.expected_revenue,
        economics=InterventionEconomics(
            intervention_cost=12.0,
            success_probability=0.35,
            retained_revenue_fraction=0.95,
        ),
    )

    payload = {
        "dataset_notice": "Synthetic dataset; metrics validate engineering only.",
        "training_samples": len(train),
        "validation_samples": len(validation),
        "champion": champion_metrics.__dict__ if hasattr(champion_metrics, "__dict__") else {
            key: getattr(champion_metrics, key)
            for key in champion_metrics.__dataclass_fields__
        },
        "challenger": challenger_metrics.__dict__ if hasattr(challenger_metrics, "__dict__") else {
            key: getattr(challenger_metrics, key)
            for key in challenger_metrics.__dataclass_fields__
        },
        "promotion": {
            "promote": promotion.promote,
            "brier_improvement": promotion.brier_improvement,
            "reasons": list(promotion.reasons),
        },
        "sample_decision": {
            "act": decision.act,
            "cancellation_probability": decision.cancellation_probability,
            "expected_loss_without_action": decision.expected_loss_without_action,
            "expected_recovered_revenue": decision.expected_recovered_revenue,
            "expected_net_value": decision.expected_net_value,
            "reason": decision.reason,
        },
    }
    output = ROOT / "m3-evaluation-output.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

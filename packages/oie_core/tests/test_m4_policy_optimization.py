from datetime import datetime, timedelta

import pytest

from oie_core.calibration import PlattCalibrator
from oie_core.decision_curve import build_decision_curve
from oie_core.decision_policy import InterventionEconomics
from oie_core.evaluation import evaluate_probabilities
from oie_core.policy_optimization import (
    DecisionCase,
    PolicySearchSpace,
    backtest_policy,
    optimize_policy,
)
from oie_core.decision_policy import DecisionPolicy


def test_platt_calibrator_improves_overconfident_probabilities() -> None:
    raw = [0.05, 0.10, 0.20, 0.80, 0.90, 0.95] * 20
    targets = [0, 0, 0, 1, 1, 1] * 20
    # Deliberately distort the raw probabilities toward extremes.
    distorted = [0.001 if p < 0.5 else 0.999 for p in raw]
    before = evaluate_probabilities(targets, distorted)
    calibrator = PlattCalibrator(epochs=1500, learning_rate=0.02)
    calibrator.fit(distorted, targets)
    calibrated = calibrator.transform(distorted)
    after = evaluate_probabilities(targets, calibrated)
    assert after.brier_score <= before.brier_score
    assert after.log_loss < before.log_loss
    assert calibrator.training_size == len(targets)


def _cases() -> list[DecisionCase]:
    start = datetime(2026, 1, 1, 8)
    rows: list[DecisionCase] = []
    for index in range(40):
        risky = index % 4 == 0
        rows.append(
            DecisionCase(
                occurred_at=start + timedelta(days=index),
                cancellation_probability=0.70 if risky else 0.08,
                cancelled=risky,
                expected_revenue=1800.0 if risky else 600.0,
            )
        )
    return rows


def test_backtest_computes_realized_policy_value() -> None:
    economics = InterventionEconomics(intervention_cost=20.0, success_probability=0.5)
    result = backtest_policy(
        _cases(),
        economics=economics,
        policy=DecisionPolicy(min_risk_probability=0.5, min_expected_net_value=1.0),
    )
    assert result.action_count == 10
    assert result.recovered_revenue == pytest.approx(9000.0)
    assert result.intervention_cost == pytest.approx(200.0)
    assert result.net_value == pytest.approx(8800.0)
    assert result.action_rate == pytest.approx(0.25)


def test_optimizer_respects_operational_action_budget() -> None:
    economics = InterventionEconomics(intervention_cost=20.0, success_probability=0.5)
    best = optimize_policy(
        _cases(),
        economics=economics,
        search_space=PolicySearchSpace(
            min_risk_probabilities=(0.05, 0.10, 0.50),
            min_expected_net_values=(0.0, 50.0),
            max_action_rate=0.30,
        ),
    )
    assert best.action_rate <= 0.30
    assert best.net_value > 0
    assert best.policy.min_risk_probability >= 0.10


def test_decision_curve_exposes_value_action_tradeoff() -> None:
    economics = InterventionEconomics(intervention_cost=20.0, success_probability=0.5)
    curve = build_decision_curve(
        _cases(),
        economics=economics,
        thresholds=(0.05, 0.10, 0.50, 0.80),
    )
    assert len(curve) == 4
    assert curve[0].action_rate >= curve[-1].action_rate
    assert curve[-1].action_rate == 0.0

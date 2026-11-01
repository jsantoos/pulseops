"""Decision-curve style summaries for operational policy analysis."""
from __future__ import annotations

from dataclasses import dataclass

from .decision_policy import InterventionEconomics
from .policy_optimization import DecisionCase, PolicyBacktest, backtest_policy
from .decision_policy import DecisionPolicy


@dataclass(frozen=True, slots=True)
class DecisionCurvePoint:
    risk_threshold: float
    net_value: float
    action_rate: float
    recovered_revenue: float


def build_decision_curve(
    cases: list[DecisionCase],
    *,
    economics: InterventionEconomics,
    thresholds: tuple[float, ...],
    min_expected_net_value: float = 0.0,
) -> tuple[DecisionCurvePoint, ...]:
    points: list[DecisionCurvePoint] = []
    for threshold in thresholds:
        result: PolicyBacktest = backtest_policy(
            cases,
            economics=economics,
            policy=DecisionPolicy(
                min_expected_net_value=min_expected_net_value,
                min_risk_probability=threshold,
            ),
        )
        points.append(
            DecisionCurvePoint(
                risk_threshold=threshold,
                net_value=result.net_value,
                action_rate=result.action_rate,
                recovered_revenue=result.recovered_revenue,
            )
        )
    return tuple(points)

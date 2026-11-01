"""Economic policy optimization and temporal backtesting for OIE decisions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from .decision_policy import DecisionPolicy, InterventionEconomics, decide_intervention


@dataclass(frozen=True, slots=True)
class DecisionCase:
    occurred_at: datetime
    cancellation_probability: float
    cancelled: bool
    expected_revenue: float

    def __post_init__(self) -> None:
        if not 0 <= self.cancellation_probability <= 1:
            raise ValueError("cancellation_probability must be between 0 and 1")
        if not isfinite(self.expected_revenue) or self.expected_revenue < 0:
            raise ValueError("expected_revenue must be finite and >= 0")


@dataclass(frozen=True, slots=True)
class PolicyBacktest:
    policy: DecisionPolicy
    sample_size: int
    action_count: int
    realized_cancellations: int
    prevented_cancellations: float
    intervention_cost: float
    recovered_revenue: float
    avoided_loss: float
    net_value: float
    action_rate: float


@dataclass(frozen=True, slots=True)
class PolicySearchSpace:
    min_risk_probabilities: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40)
    min_expected_net_values: tuple[float, ...] = (0.0, 10.0, 25.0, 50.0, 100.0)
    max_action_rate: float = 0.50
    min_actions: int = 1

    def __post_init__(self) -> None:
        if not 0 < self.max_action_rate <= 1:
            raise ValueError("max_action_rate must be in (0, 1]")
        if self.min_actions < 0:
            raise ValueError("min_actions must be >= 0")


def backtest_policy(
    cases: list[DecisionCase],
    *,
    economics: InterventionEconomics,
    policy: DecisionPolicy,
) -> PolicyBacktest:
    """Replay a fixed policy against historical outcomes.

    Expected intervention success is used for attributable recovered revenue;
    this avoids pretending synthetic/backtest replay can identify individual
    counterfactual outcomes with certainty.
    """
    if not cases:
        raise ValueError("cases must not be empty")

    action_count = 0
    realized_cancellations = 0
    prevented = 0.0
    recovered_revenue = 0.0
    intervention_cost = 0.0
    avoided_loss = 0.0

    for case in sorted(cases, key=lambda item: item.occurred_at):
        if case.cancelled:
            realized_cancellations += 1
            avoided_loss += case.expected_revenue
        decision = decide_intervention(
            cancellation_probability=case.cancellation_probability,
            expected_revenue=case.expected_revenue,
            economics=economics,
            policy=policy,
        )
        if not decision.act:
            continue
        action_count += 1
        intervention_cost += economics.intervention_cost
        if case.cancelled:
            prevented += economics.success_probability
            recovered_revenue += (
                case.expected_revenue
                * economics.success_probability
                * economics.retained_revenue_fraction
            )

    net_value = recovered_revenue - intervention_cost
    return PolicyBacktest(
        policy=policy,
        sample_size=len(cases),
        action_count=action_count,
        realized_cancellations=realized_cancellations,
        prevented_cancellations=prevented,
        intervention_cost=intervention_cost,
        recovered_revenue=recovered_revenue,
        avoided_loss=avoided_loss,
        net_value=net_value,
        action_rate=action_count / len(cases),
    )


def optimize_policy(
    cases: list[DecisionCase],
    *,
    economics: InterventionEconomics,
    search_space: PolicySearchSpace | None = None,
) -> PolicyBacktest:
    """Select the highest-value policy subject to operational constraints."""
    active = search_space or PolicySearchSpace()
    candidates: list[PolicyBacktest] = []
    for risk in active.min_risk_probabilities:
        for value in active.min_expected_net_values:
            result = backtest_policy(
                cases,
                economics=economics,
                policy=DecisionPolicy(
                    min_expected_net_value=value,
                    min_risk_probability=risk,
                ),
            )
            if result.action_rate <= active.max_action_rate and result.action_count >= active.min_actions:
                candidates.append(result)
    if not candidates:
        raise ValueError("no policy satisfies the search constraints")
    return max(
        candidates,
        key=lambda item: (
            item.net_value,
            -item.action_rate,
            item.policy.min_risk_probability,
            item.policy.min_expected_net_value,
        ),
    )

"""Economic decision policy for cancellation-risk interventions.

Prediction and decision are deliberately separated. A model estimates risk;
this module decides whether acting on that risk has positive expected value.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class InterventionEconomics:
    intervention_cost: float
    success_probability: float
    retained_revenue_fraction: float = 1.0

    def __post_init__(self) -> None:
        if not isfinite(self.intervention_cost) or self.intervention_cost < 0:
            raise ValueError("intervention_cost must be finite and >= 0")
        if not 0 <= self.success_probability <= 1:
            raise ValueError("success_probability must be between 0 and 1")
        if not 0 <= self.retained_revenue_fraction <= 1:
            raise ValueError("retained_revenue_fraction must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    min_expected_net_value: float = 1.0
    min_risk_probability: float = 0.05


@dataclass(frozen=True, slots=True)
class InterventionDecision:
    act: bool
    cancellation_probability: float
    expected_loss_without_action: float
    expected_recovered_revenue: float
    expected_net_value: float
    reason: str


def decide_intervention(
    *,
    cancellation_probability: float,
    expected_revenue: float,
    economics: InterventionEconomics,
    policy: DecisionPolicy | None = None,
) -> InterventionDecision:
    if not 0 <= cancellation_probability <= 1:
        raise ValueError("cancellation_probability must be between 0 and 1")
    if not isfinite(expected_revenue) or expected_revenue < 0:
        raise ValueError("expected_revenue must be finite and >= 0")

    active = policy or DecisionPolicy()
    expected_loss = cancellation_probability * expected_revenue
    recovered = (
        expected_loss
        * economics.success_probability
        * economics.retained_revenue_fraction
    )
    net_value = recovered - economics.intervention_cost

    if cancellation_probability < active.min_risk_probability:
        act = False
        reason = "risk below action threshold"
    elif net_value < active.min_expected_net_value:
        act = False
        reason = "expected net value below action threshold"
    else:
        act = True
        reason = "positive expected operational value"

    return InterventionDecision(
        act=act,
        cancellation_probability=cancellation_probability,
        expected_loss_without_action=expected_loss,
        expected_recovered_revenue=recovered,
        expected_net_value=net_value,
        reason=reason,
    )

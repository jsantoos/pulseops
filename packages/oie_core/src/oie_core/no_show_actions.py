"""Deterministic operational action policy for no-show risk predictions.

Prediction and action selection are deliberately separated. The ML model estimates
risk; this policy converts risk + economic impact into an operational recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NoShowActionType(StrEnum):
    NO_ACTION = "no_action"
    SEND_REMINDER = "send_reminder"
    REQUEST_CONFIRMATION = "request_confirmation"
    ACTIVE_CONFIRMATION = "active_confirmation"


@dataclass(frozen=True, slots=True)
class NoShowActionRecommendation:
    action_type: NoShowActionType
    label: str
    reason: str
    risk_level: str
    actionable: bool


def recommend_no_show_action(
    *,
    probability: float,
    expected_net_value: float,
    expected_revenue: float,
) -> NoShowActionRecommendation:
    """Select an auditable intervention from calibrated risk and economics.

    Economic value gates action first. Risk then controls intervention intensity.
    High expected net value may escalate one level because expensive slots justify
    more proactive follow-up even when probability is only moderate.
    """
    risk_level = _risk_level(probability)
    if probability < 0.20 or expected_net_value < 50.0 or expected_revenue <= 0:
        return NoShowActionRecommendation(
            NoShowActionType.NO_ACTION,
            "Apenas monitorar",
            "O risco ou o benefício econômico esperado não justificam uma intervenção agora.",
            risk_level,
            False,
        )

    if probability < 0.35:
        action = NoShowActionType.SEND_REMINDER
    elif probability < 0.55:
        action = NoShowActionType.REQUEST_CONFIRMATION
    else:
        action = NoShowActionType.ACTIVE_CONFIRMATION

    # Economic escalation: a large net benefit justifies one stronger action.
    if expected_net_value >= 1000.0:
        if action is NoShowActionType.SEND_REMINDER:
            action = NoShowActionType.REQUEST_CONFIRMATION
        elif action is NoShowActionType.REQUEST_CONFIRMATION:
            action = NoShowActionType.ACTIVE_CONFIRMATION

    label, reason = {
        NoShowActionType.SEND_REMINDER: (
            "Enviar lembrete",
            "Há risco relevante e valor econômico suficiente para um lembrete direcionado.",
        ),
        NoShowActionType.REQUEST_CONFIRMATION: (
            "Solicitar confirmação de presença",
            "O risco e o impacto esperado justificam confirmar ativamente a presença.",
        ),
        NoShowActionType.ACTIVE_CONFIRMATION: (
            "Realizar confirmação ativa",
            "O risco elevado e o impacto financeiro esperado justificam contato ativo e preparação de contingência.",
        ),
    }[action]
    return NoShowActionRecommendation(action, label, reason, risk_level, True)


def _risk_level(probability: float) -> str:
    if probability >= 0.70:
        return "critical"
    if probability >= 0.55:
        return "high"
    if probability >= 0.35:
        return "moderate"
    return "low"

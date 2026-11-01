"""Rank idle capacity for recovery actions."""
from __future__ import annotations

from dataclasses import dataclass

from .operational_models import IdleSlot


@dataclass(frozen=True, slots=True)
class SlotRecoveryCandidate:
    slot: IdleSlot
    recovery_probability: float
    expected_recovered_revenue: float
    priority_score: float


def rank_slot_recovery(
    slots: list[IdleSlot],
    *,
    recovery_probability: float = 0.50,
) -> list[SlotRecoveryCandidate]:
    if not 0.0 <= recovery_probability <= 1.0:
        raise ValueError("recovery_probability must be between 0 and 1")
    candidates = [
        SlotRecoveryCandidate(
            slot=slot,
            recovery_probability=recovery_probability,
            expected_recovered_revenue=slot.estimated_revenue * recovery_probability,
            priority_score=slot.estimated_revenue * recovery_probability,
        )
        for slot in slots
        if slot.duration_minutes > 0 and slot.estimated_revenue > 0
    ]
    return sorted(candidates, key=lambda item: item.priority_score, reverse=True)

"""Pure domain models for OIE.

This module intentionally has no ORM, web framework, or LLM dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class EquipmentSnapshot:
    """Aggregated operational facts for one equipment/resource in a period."""

    equipment_id: str
    equipment_name: str
    equipment_type: str
    available_minutes: int
    booked_minutes: int
    realized_minutes: int
    gross_revenue: float

    @property
    def utilization(self) -> float:
        if self.available_minutes <= 0:
            return 0.0
        return min(max(self.realized_minutes / self.available_minutes, 0.0), 1.0)

    @property
    def revenue_per_realized_minute(self) -> float:
        if self.realized_minutes <= 0:
            return 0.0
        return max(self.gross_revenue / self.realized_minutes, 0.0)


@dataclass(frozen=True, slots=True)
class Opportunity:
    """An actionable, auditable operational opportunity."""

    opportunity_id: str
    category: str
    title: str
    severity: Severity
    confidence: float
    estimated_gain: float
    score: float
    recommended_actions: tuple[str, ...]
    evidence: Mapping[str, float | int | str]

"""Champion/challenger governance for probabilistic OIE models."""
from __future__ import annotations

from dataclasses import dataclass

from .evaluation import ProbabilisticMetrics


@dataclass(frozen=True, slots=True)
class PromotionPolicy:
    """Guardrails for replacing a production champion.

    Lower is better for Brier score, log loss, and calibration error. A
    challenger must materially improve Brier score and may not regress the
    other probabilistic safety metrics beyond configured tolerances.
    """

    min_brier_improvement: float = 0.002
    max_log_loss_regression: float = 0.01
    max_calibration_regression: float = 0.01
    min_validation_samples: int = 30


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    promote: bool
    reasons: tuple[str, ...]
    brier_improvement: float


def evaluate_promotion(
    champion: ProbabilisticMetrics,
    challenger: ProbabilisticMetrics,
    policy: PromotionPolicy | None = None,
) -> PromotionDecision:
    active = policy or PromotionPolicy()
    reasons: list[str] = []
    brier_improvement = champion.brier_score - challenger.brier_score

    if challenger.sample_size < active.min_validation_samples:
        reasons.append(
            f"validation sample too small: {challenger.sample_size} < "
            f"{active.min_validation_samples}"
        )
    if brier_improvement < active.min_brier_improvement:
        reasons.append(
            "insufficient Brier improvement: "
            f"{brier_improvement:.6f} < {active.min_brier_improvement:.6f}"
        )
    if challenger.log_loss > champion.log_loss + active.max_log_loss_regression:
        reasons.append("log loss regression exceeds policy")
    if (
        challenger.calibration_error
        > champion.calibration_error + active.max_calibration_regression
    ):
        reasons.append("calibration regression exceeds policy")

    return PromotionDecision(
        promote=not reasons,
        reasons=tuple(reasons),
        brier_improvement=brier_improvement,
    )

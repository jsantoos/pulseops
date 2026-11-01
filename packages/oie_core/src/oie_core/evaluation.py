"""Evaluation primitives for probabilistic OIE predictors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import log

from .features import CancellationFeatures

_EPS = 1e-15


@dataclass(frozen=True, slots=True)
class ProbabilisticMetrics:
    brier_score: float
    log_loss: float
    calibration_error: float
    positive_rate: float
    sample_size: int


def temporal_split(
    rows: list[tuple[CancellationFeatures, int]],
    *,
    validation_fraction: float = 0.2,
) -> tuple[list[tuple[CancellationFeatures, int]], list[tuple[CancellationFeatures, int]]]:
    """Split chronologically to prevent future-to-past leakage."""
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if len(rows) < 2:
        raise ValueError("at least two rows are required")
    ordered = sorted(rows, key=lambda item: item[0].scheduled_at)
    validation_size = max(1, round(len(ordered) * validation_fraction))
    training_size = len(ordered) - validation_size
    if training_size < 1:
        training_size = 1
        validation_size = len(ordered) - 1
    return ordered[:training_size], ordered[training_size:]


def evaluate_probabilities(y_true: list[int], y_prob: list[float]) -> ProbabilisticMetrics:
    if len(y_true) != len(y_prob) or not y_true:
        raise ValueError("y_true and y_prob must have the same non-zero length")
    for target in y_true:
        if target not in (0, 1):
            raise ValueError("targets must be binary")
    probabilities = [min(max(float(p), _EPS), 1.0 - _EPS) for p in y_prob]
    n = len(y_true)
    brier = sum((p - y) ** 2 for y, p in zip(y_true, probabilities, strict=True)) / n
    loss = -sum(
        y * log(p) + (1 - y) * log(1 - p)
        for y, p in zip(y_true, probabilities, strict=True)
    ) / n
    # Expected calibration error with fixed 10 equal-width bins.
    ece = 0.0
    for idx in range(10):
        low, high = idx / 10.0, (idx + 1) / 10.0
        members = [
            (y, p)
            for y, p in zip(y_true, probabilities, strict=True)
            if low <= p < high or (idx == 9 and p == 1.0)
        ]
        if not members:
            continue
        observed = sum(y for y, _ in members) / len(members)
        predicted = sum(p for _, p in members) / len(members)
        ece += len(members) / n * abs(observed - predicted)
    return ProbabilisticMetrics(
        brier_score=brier,
        log_loss=loss,
        calibration_error=ece,
        positive_rate=sum(y_true) / n,
        sample_size=n,
    )

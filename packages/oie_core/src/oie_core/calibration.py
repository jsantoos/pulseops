"""Probability calibration utilities for OIE predictors.

Calibration is deliberately separated from prediction so model discrimination
and probability reliability can be evaluated independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, isfinite, log

_EPS = 1e-9


def _logit(probability: float) -> float:
    p = min(max(float(probability), _EPS), 1.0 - _EPS)
    return log(p / (1.0 - p))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1.0 / (1.0 + z)
    z = exp(value)
    return z / (1.0 + z)


@dataclass(slots=True)
class PlattCalibrator:
    """Dependency-free Platt scaling on model probabilities.

    The calibrator learns a logistic mapping over the log-odds emitted by a
    predictor. It must be fitted only on data not used to train the predictor.
    """

    learning_rate: float = 0.05
    epochs: int = 1000
    l2: float = 0.001
    version: str = "platt-v1"
    _intercept: float = field(init=False, default=0.0, repr=False)
    _slope: float = field(init=False, default=1.0, repr=False)
    _is_fitted: bool = field(init=False, default=False, repr=False)
    _training_size: int = field(init=False, default=0, repr=False)

    def __post_init__(self) -> None:
        if not isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("learning_rate must be finite and > 0")
        if self.epochs <= 0:
            raise ValueError("epochs must be > 0")
        if not isfinite(self.l2) or self.l2 < 0:
            raise ValueError("l2 must be finite and >= 0")

    def fit(self, probabilities: list[float], targets: list[int]) -> None:
        if len(probabilities) != len(targets) or not probabilities:
            raise ValueError("probabilities and targets must have equal non-zero length")
        logits = [_logit(p) for p in probabilities]
        for target in targets:
            if target not in (0, 1):
                raise ValueError("targets must be binary")

        intercept = 0.0
        slope = 1.0
        n = len(targets)
        for _ in range(self.epochs):
            grad_intercept = 0.0
            grad_slope = 0.0
            for x, target in zip(logits, targets, strict=True):
                predicted = _sigmoid(intercept + slope * x)
                error = predicted - target
                grad_intercept += error
                grad_slope += error * x
            intercept -= self.learning_rate * (grad_intercept / n)
            slope -= self.learning_rate * (grad_slope / n + self.l2 * slope)

        self._intercept = intercept
        self._slope = slope
        self._training_size = n
        self._is_fitted = True

    def transform_one(self, probability: float) -> float:
        if not self._is_fitted:
            raise RuntimeError("calibrator must be fitted before transform")
        return _sigmoid(self._intercept + self._slope * _logit(probability))

    def transform(self, probabilities: list[float]) -> list[float]:
        return [self.transform_one(p) for p in probabilities]

    @property
    def training_size(self) -> int:
        return self._training_size

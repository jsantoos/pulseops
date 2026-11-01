"""Small, dependency-free challenger models for OIE.

These models exist to validate the model-governance pipeline before introducing
heavier ML dependencies. They are deterministic for a fixed dataset and
hyperparameters and expose the same Prediction contract as the baseline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, isfinite

from .features import CancellationFeatures
from .prediction import Prediction


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1.0 / (1.0 + z)
    z = exp(value)
    return z / (1.0 + z)


@dataclass(slots=True)
class LogisticCancellationChallenger:
    """A compact logistic-regression challenger trained with batch GD.

    Categorical exam types are intentionally excluded in M3. This first
    challenger tests whether generic temporal/economic signals outperform the
    empirical Bayesian exam-type baseline. Feature expansion belongs to a
    later, separately evaluated feature-set version.
    """

    learning_rate: float = 0.05
    epochs: int = 800
    l2: float = 0.01
    model_version: str = "logistic-cancellation-challenger-v1"
    _weights: list[float] = field(init=False, default_factory=list, repr=False)
    _means: list[float] = field(init=False, default_factory=list, repr=False)
    _scales: list[float] = field(init=False, default_factory=list, repr=False)
    _is_fitted: bool = field(init=False, default=False, repr=False)
    _training_size: int = field(init=False, default=0, repr=False)

    def __post_init__(self) -> None:
        if not isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("learning_rate must be finite and > 0")
        if self.epochs <= 0:
            raise ValueError("epochs must be > 0")
        if not isfinite(self.l2) or self.l2 < 0:
            raise ValueError("l2 must be finite and >= 0")

    @staticmethod
    def _raw_features(features: CancellationFeatures) -> list[float]:
        return [
            float(features.hour_of_day),
            float(features.day_of_week),
            float(features.lead_time_days),
            float(features.expected_revenue),
        ]

    def _standardize_fit(self, matrix: list[list[float]]) -> list[list[float]]:
        width = len(matrix[0])
        means: list[float] = []
        scales: list[float] = []
        for column in range(width):
            values = [row[column] for row in matrix]
            mean = sum(values) / len(values)
            variance = sum((value - mean) ** 2 for value in values) / len(values)
            scale = variance**0.5
            means.append(mean)
            scales.append(scale if scale > 1e-12 else 1.0)
        self._means = means
        self._scales = scales
        return [self._standardize_row(row) for row in matrix]

    def _standardize_row(self, row: list[float]) -> list[float]:
        return [
            (value - mean) / scale
            for value, mean, scale in zip(row, self._means, self._scales, strict=True)
        ]

    def fit(self, rows: list[tuple[CancellationFeatures, int]]) -> None:
        if not rows:
            raise ValueError("training rows must not be empty")
        targets: list[int] = []
        raw_matrix: list[list[float]] = []
        for features, target in rows:
            if target not in (0, 1):
                raise ValueError("target must be 0 or 1")
            targets.append(target)
            raw_matrix.append(self._raw_features(features))
        matrix = self._standardize_fit(raw_matrix)
        # Intercept + standardized numeric features.
        weights = [0.0] * (len(matrix[0]) + 1)
        n = len(matrix)
        for _ in range(self.epochs):
            gradients = [0.0] * len(weights)
            for features, target in zip(matrix, targets, strict=True):
                vector = [1.0, *features]
                prediction = _sigmoid(
                    sum(weight * value for weight, value in zip(weights, vector, strict=True))
                )
                error = prediction - target
                for index, value in enumerate(vector):
                    gradients[index] += error * value
            for index in range(len(weights)):
                regularization = 0.0 if index == 0 else self.l2 * weights[index]
                weights[index] -= self.learning_rate * (
                    gradients[index] / n + regularization
                )
        self._weights = weights
        self._training_size = n
        self._is_fitted = True

    def predict_one(self, features: CancellationFeatures) -> Prediction:
        if not self._is_fitted:
            raise RuntimeError("predictor must be fitted before prediction")
        raw = self._raw_features(features)
        standardized = self._standardize_row(raw)
        vector = [1.0, *standardized]
        probability = _sigmoid(
            sum(weight * value for weight, value in zip(self._weights, vector, strict=True))
        )
        return Prediction(
            probability=min(max(probability, 0.0), 1.0),
            model_version=self.model_version,
            evidence_count=self._training_size,
        )

    def feature_contributions(self, features: CancellationFeatures) -> dict[str, float]:
        """Return local log-odds contributions from features actually used by v1."""
        if not self._is_fitted:
            raise RuntimeError("predictor must be fitted before explanation")
        standardized = self._standardize_row(self._raw_features(features))
        names = ("hour_of_day", "day_of_week", "lead_time_days", "expected_revenue")
        return {
            name: self._weights[index + 1] * value
            for index, (name, value) in enumerate(zip(names, standardized, strict=True))
        }

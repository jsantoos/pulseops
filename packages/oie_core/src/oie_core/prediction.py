"""Predictive baselines used by OIE.

The M2 predictor is intentionally simple and auditable. It uses empirical
Bayesian smoothing by exam type and falls back to the portfolio base rate.
The returned value is a model probability estimate, not an LLM judgement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from .features import CancellationFeatures


@dataclass(frozen=True, slots=True)
class Prediction:
    probability: float
    model_version: str
    evidence_count: int


@dataclass(slots=True)
class BayesianCancellationBaseline:
    prior_strength: float = 10.0
    model_version: str = "bayesian-cancellation-baseline-v1"
    _global_rate: float = field(init=False, default=0.0, repr=False)
    _counts: dict[str, tuple[int, int]] = field(init=False, default_factory=dict, repr=False)
    _is_fitted: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        if not isfinite(self.prior_strength) or self.prior_strength <= 0:
            raise ValueError("prior_strength must be finite and > 0")

    def fit(self, rows: list[tuple[CancellationFeatures, int]]) -> None:
        if not rows:
            raise ValueError("training rows must not be empty")
        positives = 0
        counts: dict[str, list[int]] = {}
        for features, target in rows:
            if target not in (0, 1):
                raise ValueError("target must be 0 or 1")
            positives += target
            bucket = counts.setdefault(features.exam_type, [0, 0])
            bucket[0] += target
            bucket[1] += 1
        self._global_rate = positives / len(rows)
        self._counts = {key: (value[0], value[1]) for key, value in counts.items()}
        self._is_fitted = True

    def predict_one(self, features: CancellationFeatures) -> Prediction:
        if not self._is_fitted:
            raise RuntimeError("predictor must be fitted before prediction")
        positives, count = self._counts.get(features.exam_type, (0, 0))
        numerator = positives + self.prior_strength * self._global_rate
        denominator = count + self.prior_strength
        probability = numerator / denominator
        return Prediction(
            probability=min(max(probability, 0.0), 1.0),
            model_version=self.model_version,
            evidence_count=count,
        )

    def exam_type_signal(self, features: CancellationFeatures) -> tuple[float, float, int]:
        """Return smoothed exam-type probability, portfolio rate and evidence count."""
        if not self._is_fitted:
            raise RuntimeError("predictor must be fitted before explanation")
        positives, count = self._counts.get(features.exam_type, (0, 0))
        probability = (positives + self.prior_strength * self._global_rate) / (count + self.prior_strength)
        return probability, self._global_rate, count

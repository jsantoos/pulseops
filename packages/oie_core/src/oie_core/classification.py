"""Threshold metrics for decision-oriented binary predictions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThresholdMetrics:
    threshold: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    precision: float
    recall: float
    specificity: float


def evaluate_threshold(
    y_true: list[int], y_prob: list[float], *, threshold: float
) -> ThresholdMetrics:
    if len(y_true) != len(y_prob) or not y_true:
        raise ValueError("y_true and y_prob must have the same non-zero length")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    tp = fp = tn = fn = 0
    for target, probability in zip(y_true, y_prob, strict=True):
        if target not in (0, 1):
            raise ValueError("targets must be binary")
        predicted = probability >= threshold
        if target == 1 and predicted:
            tp += 1
        elif target == 0 and predicted:
            fp += 1
        elif target == 0:
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return ThresholdMetrics(
        threshold=threshold,
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        precision=precision,
        recall=recall,
        specificity=specificity,
    )

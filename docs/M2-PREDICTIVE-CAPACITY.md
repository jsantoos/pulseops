# OIE M2 — Predictive Capacity & Slot Recovery

## Scope
M2 establishes the first predictive engineering contracts without making probabilistic models a hidden source of truth.

### Components
- `features.py`: versioned, leakage-safe cancellation feature extraction.
- `prediction.py`: empirical Bayesian cancellation baseline with explicit prior strength and model version.
- `evaluation.py`: chronological split, Brier score, log loss and expected calibration error.
- `slot_recovery.py`: deterministic ranking of idle slots by expected recoverable revenue.

## Promotion policy
A future challenger (e.g. logistic regression, gradient boosting) must beat the baseline on held-out chronological data and pass calibration/operational thresholds before it is considered for production.

## Explicit non-goals
- no patient-identifying features;
- no LLM-generated probabilities;
- no online training;
- no automated production model promotion;
- no claim that synthetic-data performance predicts real-world clinical operations.

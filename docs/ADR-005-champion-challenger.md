# ADR-005 — Champion/Challenger Model Governance

## Status
Accepted for M3.

## Decision
Production prediction models are never replaced solely because a challenger is
more complex or reports one better metric. Promotion requires a pre-declared
policy evaluated on future-held-out data. Brier score is the primary M3
probabilistic metric, with explicit guardrails on log loss, calibration error,
and minimum validation sample size.

## Rationale
PulseOps consumes probabilities as economic inputs. Poorly calibrated
probabilities can create bad actions even when discrimination looks good.
Governance therefore favors reliable probabilities over model novelty.

## Consequences
- Every production predictor has a versioned champion.
- Challengers are evaluated against the same temporal holdout.
- Promotion produces a machine-readable decision and reasons.
- Threshold/business-policy changes are governed separately from model changes.

# OIE M1 — Granular Operations

## Objective

Move OIE from pre-aggregated snapshots to auditable operational facts while keeping the core framework-independent and deterministic.

## New canonical facts

- `Equipment`
- `AvailabilityWindow`
- `Appointment`
- `ExamExecution`
- `IdleSlot`

No patient identity is required for M1. This is intentional data minimization.

## Deterministic pipeline

`granular facts -> validation -> aggregation -> analytics -> opportunity -> score`

The LLM remains outside the source-of-truth path.

## M1 opportunities

1. Capacity under-utilization.
2. Cancellation/no-show revenue loss.
3. Idle-slot detection primitive for the next scheduling-recovery milestone.

## AI engineering constraints

- Separate prediction from explanation.
- Every opportunity must include evidence sufficient to reproduce the calculation.
- Confidence is not presented as calibrated probability unless a model has been calibrated and evaluated.
- Training-serving skew is avoided by deriving future ML features from the same canonical data contracts used by deterministic analytics.
- No PHI/PII is required by the capacity core.

## Next milestone

OIE M2 introduces:

- exam-duration distributions;
- recoverable slot matching;
- cancellation risk feature pipeline;
- temporal train/validation/test split specification;
- baseline predictive model with calibration metrics;
- model registry metadata and deterministic fallback.

# ADR-006 — Separate Prediction from Decision Policy

## Status
Accepted for M3.

## Decision
A cancellation predictor estimates probability only. It does not decide whether
PulseOps should intervene. Intervention is performed by an economic decision
policy using predicted risk, appointment value, intervention cost, expected
intervention effectiveness, and configurable minimum expected net value.

## Rationale
A 60% cancellation probability can justify action for a high-value MRI and no
action for a low-value procedure. Encoding this distinction inside the model
would mix statistical inference with mutable business economics.

## Consequences
- Model calibration can be evaluated independently.
- Economic assumptions are explicit and auditable.
- Policies can be simulated without retraining models.
- Future clients can configure intervention economics without forking ML code.

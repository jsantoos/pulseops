# ADR-007 — Probability calibration is a separate production artifact

## Status
Accepted — M4

## Decision
Prediction and calibration are separate artifacts. A predictor may rank cases well while emitting unreliable probabilities. Any probability consumed by an economic decision policy must therefore have calibration measured on held-out, temporally later data.

The first implementation uses dependency-free Platt scaling. Calibration parameters are fitted only on data not used to fit the underlying predictor.

## Consequences
- Raw model scores must never be presented as trustworthy probabilities without evaluation.
- Calibration metrics are production gates, not dashboard decoration.
- Model version and calibrator version must eventually be logged with each decision.

# ADR-008 — Optimize decisions for operational value, not classification score

## Status
Accepted — M4

## Decision
OIE selects intervention policies using temporal backtesting and expected operational value, subject to explicit action-capacity constraints.

A model is not useful merely because it has better AUC, Brier score, precision, or recall. Its value is determined by the decisions it enables under real intervention costs, expected recovery rates, and operational budgets.

## Guardrails
- Backtests replay cases chronologically.
- Intervention capacity is explicit (`max_action_rate`).
- Counterfactual benefit is not claimed as observed fact; expected recovery is reported as modeled attribution.
- Policy optimization is performed on development/backtest windows and must be re-evaluated on later holdout periods before deployment.

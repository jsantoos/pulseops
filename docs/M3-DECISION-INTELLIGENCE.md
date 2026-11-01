# OIE M3 — Model Challenger & Decision Policy

M3 converts probabilistic risk into governed operational decisions.

## Components

1. `LogisticCancellationChallenger` — dependency-free numeric challenger.
2. `PromotionPolicy` — champion/challenger gates.
3. `ThresholdMetrics` — explicit precision/recall/specificity at an action threshold.
4. `DecisionPolicy` — expected-value intervention logic.

## Safety and AI-engineering boundaries

- Synthetic performance is engineering validation, not clinical/business proof.
- Model promotion is separated from action-policy deployment.
- A predictor returns probabilities; it does not issue operational actions.
- Probabilities used for economic decisions must be evaluated for calibration.
- No PII/PHI is required by the M3 feature set.
- LLMs remain outside numeric scoring and economic calculations.

## M3 acceptance

- All existing tests remain green.
- Challenger can fit/predict through the common prediction contract.
- Promotion rejects metric regressions and insufficient validation evidence.
- Decision policy can abstain when expected action value is negative.

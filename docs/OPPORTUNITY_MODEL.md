# Opportunity Model v0.1

An Opportunity is valid only when it is:

1. Actionable.
2. Supported by auditable evidence.
3. Associated with a measurable expected impact.
4. Assigned a confidence value distinct from impact.
5. Capable of receiving an Outcome later.

## Initial fields

- `opportunity_id`
- `category`
- `title`
- `severity`
- `confidence`
- `estimated_gain`
- `score`
- `recommended_actions`
- `evidence`

## Scoring

The ranking score is not a probability. In v0 it combines normalized financial impact, confidence, urgency, and execution ease with documented weights.

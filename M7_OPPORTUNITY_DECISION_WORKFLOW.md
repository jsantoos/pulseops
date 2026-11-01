# M7 — Opportunity Decision Workflow

This increment separates strategic opportunity decisions from measured outcomes.

## State machine

- `open`: available for manager decision.
- `accepted`: recommendation accepted and under follow-up; no result has been claimed yet.
- `dismissed`: manager decided not to pursue the opportunity.
- `measured`: accepted opportunity with an observed/measured result recorded.

## API

- `GET /v1/opportunities?status=open|accepted|dismissed|measured`
- `GET /v1/opportunities/{opportunity_id}`
- `POST /v1/opportunities/{opportunity_id}/decision`
  - `{ "decision": "accepted" | "dismissed", "notes": "..." }`
- `POST /v1/opportunities/{opportunity_id}/outcome`
  - allowed only when status is `accepted`
  - `{ "measured_gain": 123.45, "notes": "..." }`

## Product semantics

Accepting a recommendation is a managerial decision. It does **not** imply execution and does **not** create measured revenue.

The measured outcome endpoint is intentionally separate and can only close an accepted opportunity.

## Migration

`0009_opportunity_decisions` adds decision audit metadata to opportunities:

- `decision_note`
- `decided_by`
- `decided_at`

Existing measured opportunities remain valid.

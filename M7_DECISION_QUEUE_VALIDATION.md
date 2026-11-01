# PulseOps M7 — Predict → Decide validation

## Implemented

- Deterministic no-show action policy: `no_action`, `send_reminder`, `request_confirmation`, `active_confirmation`.
- Economic gating and escalation based on expected net value.
- Local model-supported explanation stored with each prediction.
- Explicit non-causality notice.
- Human decision persistence (`accepted` / `dismissed`) with optional note and actor.
- Tenant-safe decision endpoint and audit event.
- `/predict` operational queue with details, action buttons, notes and decision state.
- Runtime filtering of operational scoring to appointments after the scoring timestamp.
- Updated synthetic no-show demo dates.
- Frontend auth-provider lint issue fixed and PostCSS default export named.

## Backend/OIE validation

- `39 passed`
- `compileall`: PASS
- Alembic migration from empty SQLite DB to head: `0006_no_show_decisions`

## Frontend validation

The bundled `node_modules` from the uploaded project was not portable in the execution container, so npm gates must be executed after a clean install in the developer environment:

```bash
cd apps/web
rm -rf node_modules .next
npm ci
npm run typecheck
npm run lint
npm run build
```

## New endpoint

`POST /v1/ml/no-show/predictions/{prediction_id}/decision`

Body:

```json
{
  "decision": "accepted",
  "note": "optional operational context"
}
```

Minimum role: `manager`.

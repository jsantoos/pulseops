# PulseOps M7 — Measure / Outcomes

## Added
- `0007_no_show_outcomes` migration.
- Staged measurement lifecycle: recommendation accepted → action executed → observed outcome.
- Tenant-safe `PUT /v1/ml/no-show/predictions/{prediction_id}/outcome`.
- `GET /v1/ml/no-show/measure-summary`.
- Audit event `ml.no_show_outcome_recorded`.
- Predict UI metrics: accepted, executed, measured and measured recovered value.
- Button `Marcar ação executada` after accepting a recommendation.
- Observed outcome form becomes available after the appointment time has passed.
- `no_action` cards now label their amount as economic impact rather than action value.

## Semantics
`expected_net_value` remains a model/policy estimate. `measured_recovered_value` is an operationally recorded measurement/attribution and is never inferred automatically by the ML model.

## Validation
Backend syntax and migrations compile successfully in the artifact environment.
Full pytest/Next gates must be run in the developer environment because package registries are unavailable in the artifact runtime.

### Commands
```bash
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run pytest -q

cd apps/web
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

Expected Alembic head: `0007_no_show_outcomes`.

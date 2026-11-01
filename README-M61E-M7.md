# PulseOps M6.1E + M7 — Idempotency & No-show Risk Engine

## M6.1E — Dataset & Opportunity Idempotency

This milestone fixes duplicate ingestion and duplicate Opportunity Inbox items.

### Guarantees

- A dataset is unique per `organization_id + content_sha256`.
- Re-uploading the exact same CSV bundle reuses the existing dataset.
- Opportunities are upserted by `organization_id + oie_opportunity_id`.
- New analyses update the current opportunity instead of flooding the Inbox.
- Each distinct dataset analysis writes one immutable `opportunity_snapshot`.
- Opportunities with `estimated_gain <= 0` are not published.
- The Opportunity Inbox returns open opportunities only.
- Migration `0004_idempotency` cleans legacy duplicates before adding constraints.

## M7 — PulseOps Predict / No-show Risk Engine

The first supervised ML capability is now part of OIE.

### Leakage-safe evaluation design

Historical labeled appointments are sorted chronologically and split into:

- oldest 60%: model training;
- next 20%: challenger probability calibration;
- newest 20%: untouched validation.

The model never uses appointment outcome information as a feature. Current
features are available before the appointment starts:

- hour of day;
- day of week;
- lead time;
- expected revenue;
- exam type for the Bayesian baseline.

### Champion / challenger

- Champion baseline: empirical Bayesian rate by exam type.
- Challenger: logistic regression trained with deterministic batch gradient descent.
- Calibration: Platt scaling fitted only on the calibration window.
- Promotion requires improved Brier score without unacceptable log-loss or
  calibration regression.

### Decision intelligence

A probability by itself is not considered an operational decision. PulseOps
combines predicted risk with:

- expected slot revenue;
- intervention cost;
- intervention success probability;
- expected recovered revenue;
- expected net value.

Only positive/actionable predictions become `no_show_risk` opportunities.

### Endpoints

```text
POST /v1/ml/no-show/train/{dataset_id}
POST /v1/ml/no-show/train-latest
GET  /v1/ml/no-show/predictions
GET  /v1/ml/model-runs
```

The web application adds `/predict` with model metrics and future risk cards.

## Demo dataset

A deterministic PHI-free synthetic dataset is included under:

```text
datasets/no-show-demo/
```

Regenerate it with:

```bash
python scripts/generate_no_show_demo.py
```

It contains 400 labeled historical appointments and 28 future confirmed
appointments.

## Database migrations

```bash
uv run --package pulseops-api alembic upgrade head
```

Expected head:

```text
0005_no_show_ml
```

## Validation

```bash
uv sync --all-packages --all-groups
uv run pytest
uv run ruff check .
uv run mypy apps/api/src packages/oie_core/src
```

Frontend:

```bash
cd apps/web
npm install
npm run typecheck
npm run lint
npm run build
npm run dev
```

## Testing M7 through the UI

1. Log in and select a tenant.
2. Import the four files in `datasets/no-show-demo/`.
3. Open **Predições**.
4. Click **Treinar com dados mais recentes**.
5. Review the selected model, temporal validation metrics and future no-show
   predictions.
6. Return to **Oportunidades** to see actionable ML predictions transformed into
   OIE opportunities.

The current dataset is synthetic and metrics must never be represented as
production/customer performance.

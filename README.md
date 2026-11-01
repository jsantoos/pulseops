# PulseOps / OIE

PulseOps is the healthcare product. OIE (Operational Intelligence Engine) is the reusable decision-intelligence core.

## Current milestone: M0

Goal: transform canonical operational data into explainable, testable opportunities without depending on a web app, database, or LLM.

## Quick start

```bash
uv sync
uv run pytest
uv run ruff check .
uv run python scripts/analyze_sample.py
```

## Engineering principles

- Domain-first, framework-independent core.
- Deterministic analytics before generative AI.
- Evidence and confidence accompany every opportunity.
- Financial impact must be explicit and auditable.
- LLMs explain structured findings; they do not invent findings.
- No patient-identifying data in sample datasets.

## M2 — Predictive Capacity & Slot Recovery

M2 adds leakage-safe cancellation features, a transparent Bayesian probability baseline,
chronological evaluation (Brier/log-loss/calibration), and idle-slot recovery ranking.
Synthetic evaluation is intended to validate engineering behavior only; production claims
require representative client data and a documented model promotion gate.

Run:

```bash
PYTHONPATH=packages/oie_core/src pytest -q
PYTHONPATH=packages/oie_core/src python scripts/evaluate_m2.py
```

## Milestone M3 — Decision Intelligence

OIE now separates prediction from action. M3 adds a dependency-free logistic
challenger, temporal champion/challenger governance, threshold metrics, and an
economic decision policy based on expected net operational value. See
`docs/M3-DECISION-INTELLIGENCE.md`.


## M5.1 CSV bundle ingestion

Upload real-world-style operational exports:

```bash
curl -X POST \
  "http://127.0.0.1:8000/v1/datasets/csv-bundle?organization_id=$ORG_ID" \
  -F "equipment=@datasets/csv-sample/equipment.csv" \
  -F "availability=@datasets/csv-sample/availability.csv" \
  -F "appointments=@datasets/csv-sample/appointments.csv" \
  -F "executions=@datasets/csv-sample/executions.csv"
```

Then analyze the returned dataset id with `POST /v1/datasets/{dataset_id}/analyze`.

## M6 — PulseOps Web

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

The API should run on `http://127.0.0.1:8000` and the web app on `http://127.0.0.1:3000`.

## M6.1A — Business UX + Explainability

This milestone improves the presentation layer without changing OIE calculations:

- Portuguese business terminology for categories, statuses, actions and current OIE opportunity titles.
- Human-readable percentages, durations and BRL values.
- Opportunity priority translated into business bands while preserving the raw score for auditability.
- Explicit separation between observed data, OIE-derived calculations and assumptions/estimates.
- A "why PulseOps identified this opportunity" explanation with the current calculation chain and caveats.
- Financial values are labeled as potential/estimates rather than guaranteed revenue.
- Closed/measured opportunities no longer allow a second decision from the detail UI.

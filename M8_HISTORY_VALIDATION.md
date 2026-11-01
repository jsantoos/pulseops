# M8.2 — Operational History & Temporal Analytics

## Scope

- Reuses immutable `opportunity_snapshots`; no migration is required.
- Adds `GET /v1/opportunities/{opportunity_id}/history`.
- Calculates initial/current values, absolute and relative deltas, and trend.
- Capacity primary trend: utilization (higher is better).
- Cancellation primary trend: loss rate (lower is better).
- Opportunity detail renders historical KPI cards, sparklines, decision timestamp, and snapshot table.

## Validation

```bash
uv run pytest -q
cd apps/web
npm run typecheck
npm run lint
npm run build
```

Expected on the temporal demo after baseline + period 2 + period 3 are analyzed:

```text
capacity RM-01       snapshots=3
capacity RM-02       snapshots=3
cancellation RM-01   snapshots=3
cancellation RM-02   snapshots=3
```

Open a capacity/cancellation opportunity and confirm the **M8 · Histórico operacional** section shows three snapshots.

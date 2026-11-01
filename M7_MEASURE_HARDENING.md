# PulseOps M7 — Measure hardening

This patch closes the operational state transitions around Predict → Decide → Execute → Measure.

## User-facing behavior

- Accepted recommendation: explicit **Recomendação aceita · aguardando execução** panel and **Marcar ação executada** CTA.
- Executed action while the appointment is still in the future: explicit **Ação executada · aguardando resultado** state. No database/date manipulation is part of the product flow.
- Executed action after the scheduled time: explicit **Resultado pendente** state and **Registrar resultado** CTA, which expands the observed outcome form.
- Measured outcome: explicit **Resultado registrado ✓** state.
- Dismissed recommendation: explicit **Recomendação ignorada** state.
- Temporary prediction debug output is not present in this package.

## Prediction history vs. active queue

`no_show_predictions` intentionally preserves one row per appointment per model run for lineage. Multiple rows for the same `appointment_id` across retraining runs are therefore historical model outputs, not duplicate active queue items.

The operational API already selects only the latest no-show `model_run`; this patch adds a regression test proving that only the newest prediction for an appointment is returned to `/v1/ml/no-show/predictions` when older runs exist.

## Measure state hardening

The outcome endpoint now rejects invalid transitions:

- an executed intervention cannot be reverted to not-executed;
- an observed outcome requires `intervention_executed=true`;
- realized/recovered financial values require an observed status;
- observed status still cannot be recorded before the scheduled time;
- only accepted recommendations can be measured.

## Database

No new migration is required. Alembic head remains:

`0007_no_show_outcomes`

## Validation commands

Backend:

```bash
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run pytest -q
```

Frontend:

```bash
cd apps/web
rm -rf node_modules .next
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

## Manual browser validation

1. Train the no-show model and open `/predict`.
2. Confirm one recommendation.
3. Verify the explicit accepted/awaiting-execution panel and click **Marcar ação executada**.
4. Refresh the page and verify the executed state persists.
5. For a naturally elapsed appointment, open the item; verify **Resultado pendente** and click **Registrar resultado**.
6. Save attended/no-show/cancelled plus realized revenue and measured recovered value.
7. Refresh and verify **Resultado registrado ✓** and the Measure summary metrics.

For local automated fixtures, use a test fixture with a past `scheduled_at`; production users must never alter appointment dates through the UI merely to unlock measurement.

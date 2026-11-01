# M7 Final Validation

## Backend

```bash
cd ~/Projects/PulseOps/pulseops
sudo docker compose up -d
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run pytest -q
```

Expected migration head: `0009_opportunity_decisions`.

## Frontend

```bash
cd apps/web
rm -rf .next node_modules
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

## Functional checks

1. Oportunidades: tabs Abertas / Em acompanhamento / Mensuradas / Descartadas persist records.
2. Accepting an opportunity moves it from Abertas to Em acompanhamento without measuring it.
3. Recording an outcome moves it to Mensuradas and keeps measured gain/history visible.
4. `/opportunities/analytics` shows adoption, success, measured gain and realization rate.
5. Analytics break down results by category and equipment.
6. Predições -> Fila de ações -> intervention -> outcome -> Resultados remains functional.
7. Tenant/RBAC checks remain enforced.

## Notes

`Ganho mensurado` is an observed value associated with the measured opportunity; it is not presented as proof that the OIE recommendation caused the gain.

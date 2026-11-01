# M8.3 — Validação da evolução operacional

## Gates técnicos

```bash
cd ~/Projects/PulseOps/pulseops
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run pytest -q
```

O Alembic permanece em `0009_opportunity_decisions`; o M8.3 não cria migration.

```bash
cd apps/web
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

## Teste funcional

1. Ligue API e frontend.
2. Abra `/opportunities/evolution`.
3. Devem aparecer RM-01 e RM-02 como equipamentos.
4. Cada equipamento deve apresentar séries de Capacidade e Cancelamentos/ausências quando disponíveis.
5. Com os três datasets temporais de desenvolvimento, cada série agregada deve mostrar três snapshots.
6. RM-02 deve refletir a tendência sintética de melhora; RM-01 deve refletir piora no cenário de teste.
7. `Abrir análise` deve levar ao detalhe da oportunidade correspondente.

## Endpoint

`GET /v1/opportunities/temporal`

O endpoint é tenant-scoped e considera somente oportunidades operacionais agregadas (`capacity` e `cancellation`). Predições individuais de no-show permanecem no fluxo `/predict` e não são misturadas com a visão executiva temporal.

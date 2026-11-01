# M9 — Executive Intelligence

## Objetivo

Consolidar em uma única visão executiva os indicadores já calculados pelos módulos OIE, Temporal Intelligence e No-show Measure. O frontend não recalcula regras de negócio: consome `GET /v1/executive/summary`.

## Princípios

- Potencial financeiro continua sendo estimativa, nunca receita garantida.
- Ganho mensurado é valor observado/registrado pela operação.
- Evolução posterior à decisão é associação temporal, não causalidade.
- O dashboard operacional usa somente `capacity` e `cancellation`; previsões individuais de no-show permanecem na seção de IA.
- Todas as consultas respeitam `organization_id` e RBAC Viewer+.
- Nenhuma migration nova é necessária.

## Endpoint

`GET /v1/executive/summary`

## Tela

`/executive`

## Gate de validação

```bash
uv run pytest -q
cd apps/web
npm run typecheck
npm run lint
npm run build
```

# PulseOps M9.2 — Executive Signals + Collapsible Navigation

## Objetivo

Fechar a leitura executiva com comparação entre os dois snapshots operacionais mais recentes e melhorar a navegação principal para uso diário e demonstração ao cliente.

## Backend

`GET /v1/executive/summary` agora inclui:

- `previous_period_at`;
- `comparisons`: comparação atual x anterior por potencial operacional e indicador primário de cada equipamento;
- `decision_rows`: resumo de decisão, snapshots pós-decisão e variação observada;
- `top_priorities.status`;
- fallback de prioridades: quando não há oportunidade aberta, séries monitoradas em piora continuam visíveis.

Os cálculos continuam no backend e usam `opportunity_snapshots` imutáveis. O frontend apenas formata e apresenta os valores.

## Frontend

### Sidebar responsiva

- menu lateral desktop;
- botão para recolher/expandir;
- navegação agrupada por Operação, IA & previsões e Dados;
- estado ativo por rota;
- seletor de organização;
- perfil/role e logout no rodapé;
- drawer móvel em telas pequenas;
- a rota `/login` continua sem shell de navegação.

### Visão executiva M9.2

- `Potencial operacional monitorado` em vez de linguagem ambígua sobre oportunidades abertas;
- resumo automático de melhora/piora por equipamento;
- comparativo dos dois períodos mais recentes;
- tabela de decisões com dados pós-decisão;
- prioridades continuam úteis mesmo quando não existem decisões abertas;
- separação explícita entre potencial estimado e ganho mensurado.

## Gates recomendados

```bash
uv sync --all-packages --all-groups
uv run --package pulseops-api pytest -q

cd apps/web
npm ci
npm run typecheck
npm run lint
npm run build
```

## Validação funcional

1. Acessar `/executive`.
2. Recolher e expandir a sidebar.
3. Navegar por todas as rotas e confirmar o destaque do item ativo.
4. Confirmar que usuários sem permissão de importação não veem `Importar dados`.
5. Confirmar que o resumo executivo mostra sinais de RM-01/RM-02 coerentes com `/opportunities/evolution`.
6. Confirmar que `comparisons` usa os dois snapshots mais recentes e que a direção favorável respeita a semântica da métrica.
7. Em mobile, abrir/fechar o drawer e navegar para outra página.

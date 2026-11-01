# M7.1 — Intervention Workflow / Fila de Ações

## Objetivo
Fechar o intervalo entre a recomendação aceita e o desfecho clínico, registrando a intervenção operacional realizada pela equipe.

## Fluxo
1. ML produz uma previsão de no-show.
2. OIE recomenda uma ação.
3. Gestor aceita ou ignora a recomendação em `/predict`.
4. Recomendações aceitas aparecem em `/actions`.
5. A operação registra canal, resultado do contato e observação.
6. A intervenção fica persistida e auditada.
7. Após o horário do agendamento, o resultado observado pode ser medido em `/predict`.

## Canais
- whatsapp
- phone
- sms
- email
- other

## Resultados do contato
- confirmed
- no_response
- cancelled
- rescheduled
- unsuccessful
- other

## Migration
`0008_no_show_interventions`

A migration preserva execuções registradas no fluxo Measure anterior, migrando-as como `channel=other` e `contact_result=other`.

## API
`PUT /v1/ml/no-show/predictions/{prediction_id}/intervention`

Payload exemplo:
```json
{
  "channel": "whatsapp",
  "contact_result": "confirmed",
  "note": "Paciente confirmou presença pelo WhatsApp."
}
```

## Segurança
- requer recomendação previamente aceita;
- requer papel mínimo `manager`;
- tenant enforcement pelo backend;
- upsert idempotente por prediction;
- audit event `ml.no_show_intervention_recorded`.

## Validação realizada
- Python compileall: PASS
- Backend/OIE pytest: 46 passed
- Alembic clean DB -> `0008_no_show_interventions`: PASS
- TypeScript syntax transpilation dos arquivos alterados: PASS

O gate completo do Next (`npm run typecheck`, `lint`, `build`) deve ser executado localmente; o runtime de geração ficou sem acesso aos registries npm durante `npm ci`.

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/app/auth-provider";
import {
  decideNoShowPrediction,
  listModelRuns,
  listNoShowPredictions,
  trainLatestNoShowModel,
  recordNoShowOutcome,
  getNoShowMeasureSummary,
} from "@/lib/api";
import type { NoShowPrediction } from "@/lib/schemas";

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
const percent = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  maximumFractionDigits: 0,
});

const riskLabels: Record<string, string> = {
  low: "Baixo",
  moderate: "Moderado",
  high: "Alto",
  critical: "Crítico",
};

export default function PredictPage() {
  const { activeMembership } = useAuth();
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const canTrain = activeMembership
    ? ["owner", "admin", "manager", "analyst"].includes(activeMembership.role)
    : false;
  const canDecide = activeMembership
    ? ["owner", "admin", "manager"].includes(activeMembership.role)
    : false;

  const predictions = useQuery({
    queryKey: ["no-show-predictions", activeMembership?.organization_id],
    queryFn: listNoShowPredictions,
    enabled: Boolean(activeMembership),
  });
  const runs = useQuery({
    queryKey: ["model-runs", activeMembership?.organization_id],
    queryFn: listModelRuns,
    enabled: Boolean(activeMembership),
  });
  const measure = useQuery({
    queryKey: ["no-show-measure-summary", activeMembership?.organization_id],
    queryFn: getNoShowMeasureSummary,
    enabled: Boolean(activeMembership),
  });
  const train = useMutation({
    mutationFn: trainLatestNoShowModel,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["no-show-predictions"] }),
        queryClient.invalidateQueries({ queryKey: ["model-runs"] }),
        queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
      ]);
    },
  });
  const outcome = useMutation({
    mutationFn: ({
      predictionId,
      payload,
    }: {
      predictionId: string;
      payload: {
        intervention_executed: boolean;
        observed_status?: "attended" | "no_show" | "cancelled";
        realized_revenue?: number;
        measured_recovered_value?: number;
        note?: string;
      };
    }) => recordNoShowOutcome(predictionId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["no-show-predictions"] }),
        queryClient.invalidateQueries({ queryKey: ["no-show-measure-summary"] }),
      ]);
    },
  });
  const decision = useMutation({
    mutationFn: ({
      predictionId,
      value,
      note,
    }: {
      predictionId: string;
      value: "accepted" | "dismissed";
      note?: string;
    }) => decideNoShowPrediction(predictionId, { decision: value, note }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["no-show-predictions"] });
    },
  });

  const latestRun = runs.data?.[0];
  const currentTime = useCurrentTime();
  const items = useMemo(() => predictions.data ?? [], [predictions.data]);
  const actionable = items.filter((item) => item.action_recommended);
  const undecided = actionable.filter((item) => !item.decision);
  const expectedValue = undecided.reduce(
    (sum, item) => sum + item.expected_net_value,
    0,
  );
  const ranking = latestRun?.metrics?.selected_ranking as
    | Record<string, unknown>
    | undefined;
  const challenger = latestRun?.metrics?.challenger as
    | Record<string, unknown>
    | undefined;

  const sortedItems = useMemo(
    () => [...items].sort((a, b) => b.expected_net_value - a.expected_net_value),
    [items],
  );

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            PulseOps Predict · M7
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Fila de risco de no-show
          </h1>
          <p className="mt-3 text-[var(--muted)]">
            O ML estima o risco. O OIE combina a probabilidade com impacto econômico
            e transforma a previsão em uma ação operacional priorizada.
          </p>
        </div>
        {canTrain && (
          <button
            className="button-primary rounded-xl px-5 py-3 font-semibold"
            disabled={train.isPending}
            onClick={() => train.mutate()}
          >
            {train.isPending
              ? "Treinando e avaliando…"
              : "Treinar com dados mais recentes"}
          </button>
        )}
      </div>

      {train.isError && (
        <div className="mt-6 rounded-2xl bg-red-50 p-4 text-sm text-red-800">
          {train.error.message}
        </div>
      )}
      {decision.isError && (
        <div className="mt-6 rounded-2xl bg-red-50 p-4 text-sm text-red-800">
          {decision.error.message}
        </div>
      )}
      {outcome.isError && (
        <div className="mt-6 rounded-2xl bg-red-50 p-4 text-sm text-red-800">
          {outcome.error.message}
        </div>
      )}

      <section className="mt-8 grid gap-4 md:grid-cols-4">
        <Metric label="Agendamentos avaliados" value={String(items.length)} />
        <Metric label="Ações pendentes" value={String(undecided.length)} />
        <Metric label="Valor líquido priorizado" value={money.format(expectedValue)} />
        <Metric
          label="ROC-AUC validação"
          value={
            typeof ranking?.roc_auc === "number"
              ? ranking.roc_auc.toFixed(3)
              : "—"
          }
        />
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-4">
        <Metric label="Ações aceitas" value={String(measure.data?.accepted_actions ?? 0)} />
        <Metric label="Ações executadas" value={String(measure.data?.executed_actions ?? 0)} />
        <Metric label="Resultados medidos" value={String(measure.data?.measured_outcomes ?? 0)} />
        <Metric label="Valor recuperado medido" value={money.format(measure.data?.measured_recovered_value ?? 0)} />
      </section>

      {latestRun && (
        <section className="mt-6 rounded-2xl border border-[var(--border)] bg-white p-5 text-sm">
          <div className="font-semibold">Modelo ativo e governança</div>
          <div className="mt-3 grid gap-4 text-[var(--muted)] sm:grid-cols-3 lg:grid-cols-4">
            <Gov label="Versão" value={latestRun.selected_model_version} />
            <Gov label="Feature set" value={latestRun.feature_set_version} />
            <Gov
              label="Treino / calibração / validação"
              value={`${latestRun.training_rows} / ${latestRun.calibration_rows} / ${latestRun.validation_rows}`}
            />
            <Gov
              label="PR-AUC"
              value={numberMetric(ranking?.pr_auc, 3)}
            />
            <Gov
              label="Lift @ 10%"
              value={
                typeof ranking?.lift_at_10pct === "number"
                  ? `${ranking.lift_at_10pct.toFixed(2)}×`
                  : "—"
              }
            />
            <Gov
              label="Brier score"
              value={numberMetric(challenger?.brier_score, 3)}
            />
            <Gov label="Validação" value="Temporal" />
            <Gov
              label="Treinado em"
              value={new Date(latestRun.created_at).toLocaleString("pt-BR")}
            />
          </div>
          <p className="mt-4 text-xs text-[var(--muted)]">
            As explicações descrevem associações do modelo, não causalidade. A decisão
            operacional combina risco calibrado, valor econômico e política explícita.
          </p>
        </section>
      )}

      <section className="mt-6 space-y-4">
        {items.length === 0 && (
          <div className="rounded-2xl border border-dashed border-[var(--border)] bg-white p-10 text-center text-[var(--muted)]">
            Nenhuma predição disponível. Importe um histórico com pelo menos 40
            atendimentos concluídos/no-show e treine o modelo.
          </div>
        )}
        {sortedItems.map((item) => {
          const expanded = expandedId === item.id;
          const isPendingDecision =
            decision.isPending && decision.variables?.predictionId === item.id;
          const scheduledHasPassed =
            currentTime !== null &&
            new Date(item.scheduled_at).getTime() <= currentTime;
          const hasMeasuredOutcome = Boolean(item.outcome?.observed_status);
          return (
            <article
              key={item.id}
              className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap justify-between gap-5">
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                    {item.equipment_id} · {new Date(item.scheduled_at).toLocaleString("pt-BR")}
                  </div>
                  <h2 className="mt-2 text-xl font-semibold">
                    Agendamento {item.appointment_id}
                  </h2>
                  <div className="mt-3 flex flex-wrap gap-2 text-sm">
                    <span className="rounded-full bg-red-50 px-3 py-1 font-semibold text-red-700">
                      Risco {percent.format(item.probability)} · {riskLabels[item.risk_level] ?? item.risk_level}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1">
                      Receita {money.format(item.expected_revenue)}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1">
                      Perda esperada {money.format(item.expected_loss)}
                    </span>
                  </div>

                  <div className="mt-5 rounded-xl bg-slate-50 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                      Ação recomendada
                    </div>
                    <div className="mt-1 text-lg font-semibold">
                      {item.recommended_action_label}
                    </div>
                    <p className="mt-1 text-sm text-[var(--muted)]">
                      {item.recommendation_reason}
                    </p>
                  </div>
                </div>

                <div className="min-w-52 text-right">
                  <div className="text-xs uppercase text-[var(--muted)]">
                    {item.action_recommended ? "Valor líquido esperado da ação" : "Impacto econômico estimado"}
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {money.format(item.expected_net_value)}
                  </div>
                  <DecisionBadge prediction={item} currentTime={currentTime} />
                </div>
              </div>

              <WorkflowStatePanel
                prediction={item}
                canDecide={canDecide}
                scheduledHasPassed={scheduledHasPassed}
                hasMeasuredOutcome={hasMeasuredOutcome}
                onOpenOutcome={() => setExpandedId(item.id)}
              />

              {expanded && (
                <PredictionDetails
                  prediction={item}
                  note={notes[item.id] ?? ""}
                  onNote={(value) =>
                    setNotes((current) => ({ ...current, [item.id]: value }))
                  }
                />
              )}

              {expanded && item.intervention && scheduledHasPassed && (
                <ObservedOutcomeForm
                  prediction={item}
                  saving={outcome.isPending}
                  onSave={(payload) => outcome.mutate({ predictionId: item.id, payload })}
                />
              )}

              <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] pt-4">
                <button
                  className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-medium hover:bg-slate-50"
                  onClick={() => setExpandedId(expanded ? null : item.id)}
                >
                  {expanded ? "Ocultar detalhes" : "Ver detalhes"}
                </button>

                {canDecide && item.action_recommended && !item.decision && (
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-medium hover:bg-slate-50"
                      disabled={isPendingDecision}
                      onClick={() =>
                        decision.mutate({
                          predictionId: item.id,
                          value: "dismissed",
                          note: notes[item.id]?.trim() || undefined,
                        })
                      }
                    >
                      Ignorar
                    </button>
                    <button
                      className="button-primary rounded-lg px-4 py-2 text-sm font-semibold"
                      disabled={isPendingDecision}
                      onClick={() =>
                        decision.mutate({
                          predictionId: item.id,
                          value: "accepted",
                          note: notes[item.id]?.trim() || undefined,
                        })
                      }
                    >
                      {isPendingDecision ? "Registrando…" : "Confirmar ação"}
                    </button>
                  </div>
                )}

                {item.intervention && (
                  <span className="text-sm font-semibold text-emerald-700">
                    {hasMeasuredOutcome ? "Resultado registrado ✓" : "Intervenção registrada ✓"}
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}


function WorkflowStatePanel({
  prediction,
  canDecide,
  scheduledHasPassed,
  hasMeasuredOutcome,
  onOpenOutcome,
}: {
  prediction: NoShowPrediction;
  canDecide: boolean;
  scheduledHasPassed: boolean;
  hasMeasuredOutcome: boolean;
  onOpenOutcome: () => void;
}) {
  if (prediction.decision?.decision === "dismissed") {
    return (
      <section className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="text-sm font-semibold text-slate-700">Recomendação ignorada</div>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Nenhuma intervenção operacional será acompanhada para esta recomendação.
        </p>
      </section>
    );
  }

  if (prediction.decision?.decision !== "accepted") return null;

  if (!prediction.intervention) {
    return (
      <section className="mt-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-blue-200 bg-blue-50/70 p-4">
        <div>
          <div className="text-sm font-semibold text-blue-900">Recomendação aceita · intervenção pendente</div>
          <p className="mt-1 text-sm text-blue-900/70">
            A recepção deve registrar o contato realizado, o canal usado e a resposta do paciente.
          </p>
        </div>
        {canDecide && (
          <Link href="/actions" className="button-primary rounded-lg px-4 py-2 text-sm font-semibold">
            Ir para fila de ações
          </Link>
        )}
      </section>
    );
  }

  if (hasMeasuredOutcome) {
    return (
      <section className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
        <div className="text-sm font-semibold text-emerald-900">Resultado registrado ✓</div>
        <p className="mt-1 text-sm text-emerald-900/70">
          O contato e o desfecho observado já estão incluídos nos indicadores de resultado.
        </p>
      </section>
    );
  }

  if (scheduledHasPassed) {
    return (
      <section className="mt-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50/70 p-4">
        <div>
          <div className="text-sm font-semibold text-amber-900">Resultado pendente</div>
          <p className="mt-1 text-sm text-amber-900/70">
            A intervenção foi registrada e o horário já ocorreu. Registre o desfecho real.
          </p>
        </div>
        <button className="button-primary rounded-lg px-4 py-2 text-sm font-semibold" onClick={onOpenOutcome}>
          Registrar resultado
        </button>
      </section>
    );
  }

  return (
    <section className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50/60 p-4">
      <div className="text-sm font-semibold text-emerald-900">Intervenção registrada · aguardando atendimento</div>
      <p className="mt-1 text-sm text-emerald-900/70">
        {interventionSummary(prediction)}. O PulseOps liberará a mensuração após o horário agendado.
      </p>
    </section>
  );
}

function interventionSummary(prediction: NoShowPrediction): string {
  const intervention = prediction.intervention;
  if (!intervention) return "Intervenção ainda não registrada";
  const channels: Record<string, string> = { whatsapp: "WhatsApp", phone: "telefone", sms: "SMS", email: "e-mail", other: "outro canal" };
  const results: Record<string, string> = { confirmed: "presença confirmada", no_response: "sem resposta", cancelled: "cancelamento informado", rescheduled: "reagendamento solicitado", unsuccessful: "contato sem sucesso", other: "outro resultado" };
  return `${channels[intervention.channel] ?? intervention.channel}: ${results[intervention.contact_result] ?? intervention.contact_result}`;
}

function PredictionDetails({
  prediction,
  note,
  onNote,
}: {
  prediction: NoShowPrediction;
  note: string;
  onNote: (value: string) => void;
}) {
  const explanation = prediction.evidence.explanation as
    | { summary?: string; factors?: unknown[] }
    | undefined;
  const factors = Array.isArray(explanation?.factors)
    ? (explanation.factors as Array<Record<string, unknown>>)
    : [];

  return (
    <div className="mt-5 grid gap-4 lg:grid-cols-2">
      <section className="rounded-xl border border-[var(--border)] p-4">
        <div className="text-sm font-semibold">Por que este risco?</div>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {explanation?.summary ??
            "O risco foi calculado com as features operacionais disponíveis antes do horário agendado."}
        </p>
        <div className="mt-3 space-y-2">
          {factors.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              Nenhum fator local adicional foi disponibilizado por este modelo.
            </p>
          ) : (
            factors.map((factor, index) => (
              <div
                key={`${String(factor.feature ?? "factor")}-${index}`}
                className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-3 py-2 text-sm"
              >
                <span>{String(factor.label ?? factor.feature ?? "Fator")}</span>
                <span
                  className={
                    factor.direction === "increase"
                      ? "font-semibold text-red-700"
                      : "font-semibold text-emerald-700"
                  }
                >
                  {factor.direction === "increase" ? "↑ aumenta associação" : "↓ reduz associação"}
                </span>
              </div>
            ))
          )}
        </div>
        <p className="mt-3 text-xs text-[var(--muted)]">
          {String(
            prediction.evidence.association_notice ??
              "Os fatores representam associações do modelo e não comprovam causalidade.",
          )}
        </p>
      </section>

      <section className="rounded-xl border border-[var(--border)] p-4">
        <div className="text-sm font-semibold">Impacto e decisão</div>
        <dl className="mt-3 space-y-2 text-sm">
          <Row label="Probabilidade calibrada" value={percent.format(prediction.probability)} />
          <Row label="Receita do horário" value={money.format(prediction.expected_revenue)} />
          <Row label="Perda esperada sem ação" value={money.format(prediction.expected_loss)} />
          <Row label="Receita esperada recuperada" value={money.format(prediction.expected_recovered_revenue)} />
          <Row label="Valor líquido esperado" value={money.format(prediction.expected_net_value)} />
        </dl>
        {!prediction.decision && prediction.action_recommended && (
          <label className="mt-4 block text-sm">
            <span className="font-medium">Observação opcional</span>
            <textarea
              value={note}
              onChange={(event) => onNote(event.target.value)}
              maxLength={2000}
              rows={3}
              placeholder="Ex.: paciente será contatado pela recepção às 14h."
              className="mt-2 w-full rounded-lg border border-[var(--border)] p-3 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
          </label>
        )}
      </section>
    </div>
  );
}

function ObservedOutcomeForm({
  prediction,
  saving,
  onSave,
}: {
  prediction: NoShowPrediction;
  saving: boolean;
  onSave: (payload: {
    intervention_executed: boolean;
    observed_status: "attended" | "no_show" | "cancelled";
    realized_revenue?: number;
    measured_recovered_value?: number;
    note?: string;
  }) => void;
}) {
  const [status, setStatus] = useState<"attended" | "no_show" | "cancelled">(
    (prediction.outcome?.observed_status as "attended" | "no_show" | "cancelled" | null) ?? "attended",
  );
  const [realizedRevenue, setRealizedRevenue] = useState(
    prediction.outcome?.realized_revenue?.toString() ?? "",
  );
  const [recoveredValue, setRecoveredValue] = useState(
    prediction.outcome?.measured_recovered_value?.toString() ?? "",
  );
  const [note, setNote] = useState(prediction.outcome?.note ?? "");

  return (
    <section className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
      <div className="text-sm font-semibold text-emerald-900">Medir resultado observado</div>
      <p className="mt-1 text-sm text-emerald-900/70">
        O horário já ocorreu. Registre o desfecho real para comparar previsão, decisão e resultado.
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <label className="text-sm">
          <span className="font-medium">Desfecho</span>
          <select value={status} onChange={(e) => setStatus(e.target.value as typeof status)} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2">
            <option value="attended">Compareceu</option>
            <option value="no_show">Não compareceu</option>
            <option value="cancelled">Cancelou</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="font-medium">Receita realizada (R$)</span>
          <input type="number" min="0" step="0.01" value={realizedRevenue} onChange={(e) => setRealizedRevenue(e.target.value)} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2" />
        </label>
        <label className="text-sm">
          <span className="font-medium">Valor recuperado medido (R$)</span>
          <input type="number" min="0" step="0.01" value={recoveredValue} onChange={(e) => setRecoveredValue(e.target.value)} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2" />
        </label>
      </div>
      <label className="mt-3 block text-sm">
        <span className="font-medium">Observação</span>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} maxLength={2000} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2" />
      </label>
      <div className="mt-3 flex items-center justify-between gap-3">
        <span className="text-xs text-[var(--muted)]">Valor recuperado é medido/atribuído pela operação; não é inferido automaticamente pelo ML.</span>
        <button className="button-primary rounded-lg px-4 py-2 text-sm font-semibold" disabled={saving} onClick={() => onSave({
          intervention_executed: true, observed_status: status,
          realized_revenue: realizedRevenue === "" ? undefined : Number(realizedRevenue),
          measured_recovered_value: recoveredValue === "" ? undefined : Number(recoveredValue),
          note: note.trim() || undefined,
        })}>
          {saving ? "Salvando…" : "Salvar resultado"}
        </button>
      </div>
    </section>
  );
}

function useCurrentTime(): number | null {
  const [currentTime, setCurrentTime] = useState<number | null>(null);

  useEffect(() => {
    const updateCurrentTime = () => setCurrentTime(Date.now());
    const initialUpdate = window.setTimeout(updateCurrentTime, 0);
    const interval = window.setInterval(updateCurrentTime, 60_000);

    return () => {
      window.clearTimeout(initialUpdate);
      window.clearInterval(interval);
    };
  }, []);

  return currentTime;
}

function DecisionBadge({
  prediction,
  currentTime,
}: {
  prediction: NoShowPrediction;
  currentTime: number | null;
}) {
  if (prediction.outcome?.observed_status) {
    return <div className="mt-2 text-sm font-semibold text-emerald-700">Resultado registrado</div>;
  }
  if (prediction.intervention) {
    const scheduledHasPassed =
      currentTime !== null &&
      new Date(prediction.scheduled_at).getTime() <= currentTime;
    return (
      <div className="mt-2 text-sm font-semibold text-emerald-700">
        {scheduledHasPassed ? "Resultado pendente" : "Intervenção registrada · aguardando atendimento"}
      </div>
    );
  }
  if (prediction.decision?.decision === "accepted") {
    return (
      <div className="mt-2 text-sm font-semibold text-emerald-700">
        Ação confirmada · aguardando execução
      </div>
    );
  }
  if (prediction.decision?.decision === "dismissed") {
    return <div className="mt-2 text-sm font-semibold text-slate-500">Ignorada</div>;
  }
  return (
    <div className="mt-2 text-sm text-[var(--muted)]">
      {prediction.action_recommended ? "Decisão pendente" : "Apenas monitorar"}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-5">
      <div className="text-sm text-[var(--muted)]">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Gov({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="block text-xs uppercase">{label}</span>
      <strong className="text-[var(--foreground)]">{value}</strong>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

function numberMetric(value: unknown, digits: number): string {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/app/auth-provider";
import { decideOpportunity, getOpportunity, getOpportunityHistory, recordOpportunityOutcome } from "@/lib/api";
import { currency, percentage } from "@/lib/format";
import { OpportunityHistoryPanel } from "@/components/opportunity-history";
import {
  actionLabel, categoryLabel, evidenceKindLabel, explanation, opportunityTitle,
  presentedEvidence, priorityLevel, severityLabel, statusLabel,
} from "@/lib/opportunity-presentation";

export default function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { activeMembership } = useAuth();
  const queryClient = useQueryClient();
  const [decisionNotes, setDecisionNotes] = useState("");
  const [outcomeNotes, setOutcomeNotes] = useState("");
  const [measuredGain, setMeasuredGain] = useState("");

  const query = useQuery({ queryKey: ["opportunity", id], queryFn: () => getOpportunity(id) });
  const history = useQuery({ queryKey: ["opportunity-history", id], queryFn: () => getOpportunityHistory(id) });
  const decision = useMutation({
    mutationFn: (value: "accepted" | "dismissed") =>
      decideOpportunity(id, { decision: value, notes: decisionNotes.trim() || undefined }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["opportunity", id] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-history", id] }),
        queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-analytics"] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-temporal"] }),
      ]);
    },
  });
  const outcome = useMutation({
    mutationFn: () => recordOpportunityOutcome(id, {
      measured_gain: measuredGain === "" ? undefined : Number(measuredGain),
      notes: outcomeNotes.trim() || undefined,
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["opportunity", id] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-history", id] }),
        queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-analytics"] }),
        queryClient.invalidateQueries({ queryKey: ["opportunity-temporal"] }),
      ]);
    },
  });

  if (query.isPending) return <main className="mx-auto max-w-5xl px-6 py-10">Carregando…</main>;
  if (query.isError) return <main className="mx-auto max-w-5xl px-6 py-10 text-red-700">{query.error.message}</main>;
  const opportunity = query.data;
  const priority = priorityLevel(opportunity.score);
  const evidence = presentedEvidence(opportunity);
  const why = explanation(opportunity);
  const canDecideRole = activeMembership ? ["owner", "admin", "manager"].includes(activeMembership.role) : false;
  const canDecide = opportunity.status === "open" && canDecideRole;
  const canMeasure = opportunity.status === "accepted" && canDecideRole;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/" className="text-sm text-[var(--accent)]">← Voltar para oportunidades</Link>
      <div className="mt-5 rounded-3xl border border-[var(--border)] bg-white p-8 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-2xl"><p className="text-sm uppercase tracking-[0.16em] text-[var(--muted)]">{categoryLabel(opportunity.category)} · Severidade {severityLabel(opportunity.severity)}</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">{opportunityTitle(opportunity)}</h1></div>
          <div className="text-right"><p className="text-sm text-[var(--muted)]">Potencial financeiro</p><p className="text-3xl font-semibold">{currency(opportunity.estimated_gain)}</p><p className="mt-1 text-xs text-[var(--muted)]">estimativa, não receita garantida</p></div>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-3"><Metric label="Prioridade" value={`${priority.label} · ${opportunity.score.toFixed(2)}`} helper={priority.description} /><Metric label="Confiança da evidência" value={percentage(opportunity.confidence)} helper="Força da evidência disponível; não é probabilidade de ganho financeiro." /><Metric label="Status" value={statusLabel(opportunity.status)} helper="Etapa atual no ciclo de decisão e medição." /></div>

        <section className="mt-8 rounded-2xl border border-[var(--accent-soft)] bg-[var(--accent-soft)]/50 p-6"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">Por que o PulseOps identificou esta oportunidade?</p><h2 className="mt-2 text-xl font-semibold">{why.headline}</h2><p className="mt-3 leading-7 text-[var(--muted)]">{why.body}</p>{why.formula && <div className="mt-4 rounded-xl bg-white px-4 py-3 font-semibold tabular-nums">{why.formula}</div>}<p className="mt-3 text-sm text-[var(--muted)]">{why.caveat}</p></section>

        <section className="mt-8"><h2 className="text-lg font-semibold">Evidências</h2><p className="mt-1 text-sm text-[var(--muted)]">Diferenciamos dados observados, cálculos do OIE e premissas usadas na estimativa.</p><dl className="mt-4 grid gap-3 sm:grid-cols-2">{evidence.map((item) => <div key={item.key} className="rounded-xl bg-slate-50 p-4"><div className="flex items-start justify-between gap-3"><dt className="text-xs uppercase tracking-wide text-[var(--muted)]">{item.label}</dt><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${item.kind === "observed" ? "bg-white text-slate-600" : item.kind === "derived" ? "bg-blue-50 text-blue-700" : "bg-amber-50 text-amber-700"}`}>{evidenceKindLabel(item.kind)}</span></div><dd className="mt-2 text-lg font-semibold">{item.value}</dd></div>)}</dl></section>

        {history.isPending && <div className="mt-8 rounded-2xl border border-[var(--border)] bg-white p-6 text-sm text-[var(--muted)]">Carregando histórico operacional…</div>}
        {history.isError && <div className="mt-8 rounded-2xl bg-red-50 p-5 text-sm text-red-800">Não foi possível carregar o histórico: {history.error.message}</div>}
        {history.data && <OpportunityHistoryPanel history={history.data} />}

        <section className="mt-8"><h2 className="text-lg font-semibold">Ações recomendadas</h2><p className="mt-1 text-sm text-[var(--muted)]">Sugestões para avaliação do responsável operacional; a execução permanece sob decisão humana.</p><ol className="mt-3 space-y-3">{opportunity.recommended_actions.map((action, index) => <li key={action} className="flex gap-3 rounded-xl border border-[var(--border)] p-4"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">{index + 1}</span><span>{actionLabel(action)}</span></li>)}</ol></section>

        {canDecide && <section className="mt-8 border-t border-[var(--border)] pt-6"><h2 className="text-lg font-semibold">Decisão gerencial</h2><p className="mt-1 text-sm text-[var(--muted)]">Aceitar coloca a oportunidade em acompanhamento. Isso ainda não significa que o resultado foi medido.</p><textarea value={decisionNotes} onChange={(e) => setDecisionNotes(e.target.value)} rows={3} className="mt-4 w-full rounded-xl border border-[var(--border)] p-3" placeholder="Contexto da decisão (opcional)"/><div className="mt-4 flex gap-3"><button disabled={decision.isPending} onClick={() => decision.mutate("accepted")} className="button-primary rounded-xl px-5 py-3 font-semibold">Aceitar recomendação</button><button disabled={decision.isPending} onClick={() => decision.mutate("dismissed")} className="rounded-xl border border-[var(--border)] px-5 py-3 font-semibold">Descartar</button></div>{decision.isError && <p className="mt-3 text-sm text-red-700">{decision.error.message}</p>}</section>}

        {opportunity.status === "accepted" && <section className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6"><h2 className="text-lg font-semibold text-emerald-900">Recomendação aceita · em acompanhamento</h2><p className="mt-2 text-sm text-emerald-800">A decisão foi registrada. Quando houver evidência do resultado, registre o ganho mensurado abaixo.</p>{opportunity.decision_note && <p className="mt-3 rounded-xl bg-white p-3 text-sm">Decisão: {opportunity.decision_note}</p>}</section>}

        {canMeasure && <section className="mt-6 border-t border-[var(--border)] pt-6"><h2 className="text-lg font-semibold">Registrar resultado da oportunidade</h2><p className="mt-1 text-sm text-[var(--muted)]">Informe apenas resultado efetivamente observado. O potencial financeiro acima continua sendo uma estimativa.</p><label className="mt-4 block text-sm font-medium">Ganho mensurado (R$)</label><input type="number" min="0" step="0.01" value={measuredGain} onChange={(e) => setMeasuredGain(e.target.value)} className="mt-2 w-full rounded-xl border border-[var(--border)] p-3" placeholder="0,00"/><label className="mt-4 block text-sm font-medium">Observação do resultado</label><textarea value={outcomeNotes} onChange={(e) => setOutcomeNotes(e.target.value)} rows={3} className="mt-2 w-full rounded-xl border border-[var(--border)] p-3" placeholder="Descreva como o resultado foi medido."/><button disabled={outcome.isPending} onClick={() => outcome.mutate()} className="button-primary mt-4 rounded-xl px-5 py-3 font-semibold">Registrar resultado mensurado</button>{outcome.isError && <p className="mt-3 text-sm text-red-700">{outcome.error.message}</p>}</section>}

        {opportunity.status === "dismissed" && <section className="mt-8 rounded-2xl bg-slate-50 p-5 text-sm text-[var(--muted)]">Oportunidade descartada. A decisão permanece registrada para auditoria.</section>}
        {opportunity.status === "measured" && <section className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6"><h2 className="text-lg font-semibold text-emerald-900">Resultado mensurado ✓</h2><div className="mt-4 grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-white p-4"><p className="text-xs uppercase text-[var(--muted)]">Ganho mensurado</p><p className="mt-1 text-2xl font-semibold text-emerald-900">{currency(opportunity.measured_gain ?? 0)}</p></div><div className="rounded-xl bg-white p-4"><p className="text-xs uppercase text-[var(--muted)]">Realização do potencial</p><p className="mt-1 text-2xl font-semibold text-emerald-900">{percentage(opportunity.estimated_gain > 0 ? (opportunity.measured_gain ?? 0) / opportunity.estimated_gain : 0)}</p></div></div>{opportunity.outcome_notes && <p className="mt-4 rounded-xl bg-white p-4 text-sm text-emerald-900">Resultado: {opportunity.outcome_notes}</p>}{opportunity.outcome_recorded_at && <p className="mt-3 text-xs text-emerald-800">Registrado em {new Date(opportunity.outcome_recorded_at).toLocaleString("pt-BR")}</p>}<Link href="/opportunities/analytics" className="mt-4 inline-block font-semibold text-[var(--accent)]">Ver analytics de oportunidades →</Link></section>}
      </div>
    </main>
  );
}

function Metric({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
      {helper && <p className="mt-2 text-xs leading-5 text-[var(--muted)]">{helper}</p>}
    </div>
  );
}

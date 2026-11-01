"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { listOpportunities } from "@/lib/api";
import { currency } from "@/lib/format";
import { categoryLabel, opportunityTitle, priorityLevel } from "@/lib/opportunity-presentation";
import type { Opportunity } from "@/lib/schemas";
import { OpportunityCard } from "./opportunity-card";

const tabs = [
  { key: "open", label: "Abertas" },
  { key: "accepted", label: "Em acompanhamento" },
  { key: "measured", label: "Mensuradas" },
  { key: "dismissed", label: "Descartadas" },
] as const;

type OpportunityStatus = (typeof tabs)[number]["key"];

export function OpportunityInbox() {
  const [activeStatus, setActiveStatus] = useState<OpportunityStatus>("open");
  const openQuery = useQuery({ queryKey: ["opportunities", "open"], queryFn: () => listOpportunities("open") });
  const acceptedQuery = useQuery({ queryKey: ["opportunities", "accepted"], queryFn: () => listOpportunities("accepted") });
  const measuredQuery = useQuery({ queryKey: ["opportunities", "measured"], queryFn: () => listOpportunities("measured") });
  const dismissedQuery = useQuery({ queryKey: ["opportunities", "dismissed"], queryFn: () => listOpportunities("dismissed") });

  const queries = { open: openQuery, accepted: acceptedQuery, measured: measuredQuery, dismissed: dismissedQuery };
  const currentQuery = queries[activeStatus];

  if (Object.values(queries).some((query) => query.isPending)) {
    return <div className="rounded-2xl border border-[var(--border)] bg-white p-8">Carregando oportunidades…</div>;
  }
  const failed = Object.values(queries).find((query) => query.isError);
  if (failed) {
    return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800">Não foi possível carregar as oportunidades: {failed.error?.message}</div>;
  }

  const open = [...(openQuery.data ?? [])].sort((a, b) => b.score - a.score);
  const current = [...(currentQuery.data ?? [])].sort((a, b) => b.score - a.score);
  const total = open.reduce((sum, item) => sum + item.estimated_gain, 0);
  const top = open[0];
  const topPriority = top ? priorityLevel(top.score) : undefined;
  const counts: Record<OpportunityStatus, number> = {
    open: open.length,
    accepted: acceptedQuery.data?.length ?? 0,
    measured: measuredQuery.data?.length ?? 0,
    dismissed: dismissedQuery.data?.length ?? 0,
  };

  return (
    <>
      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Oportunidades abertas</p>
          <p className="mt-2 text-3xl font-semibold">{open.length}</p>
          <p className="mt-2 text-xs text-[var(--muted)]">Itens atualmente disponíveis para decisão.</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Potencial financeiro identificado</p>
          <p className="mt-2 text-3xl font-semibold">{currency(total)}</p>
          <p className="mt-2 text-xs text-[var(--muted)]">Soma das estimativas abertas; não representa receita garantida.</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-white p-5">
          <p className="text-sm text-[var(--muted)]">Maior prioridade agora</p>
          {top ? (
            <>
              <p className="mt-2 text-2xl font-semibold">{topPriority?.label}</p>
              <p className="mt-1 text-sm font-medium">{opportunityTitle(top)}</p>
              <p className="mt-1 text-xs text-[var(--muted)]">{categoryLabel(top.category)} · índice {top.score.toFixed(2)}</p>
            </>
          ) : <p className="mt-2 text-3xl font-semibold">—</p>}
        </div>
      </section>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Status das oportunidades">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveStatus(tab.key)}
              className={`rounded-xl px-4 py-2 text-sm font-semibold ${activeStatus === tab.key ? "bg-[var(--accent)] text-white" : "border border-[var(--border)] bg-white hover:bg-slate-50"}`}
            >
              {tab.label} · {counts[tab.key]}
            </button>
          ))}
        </div>
        <Link href="/opportunities/analytics" className="button-primary rounded-xl px-4 py-2 text-sm font-semibold">
          Ver analytics de oportunidades
        </Link>
      </div>

      <section className="mt-6 space-y-4">
        {current.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[var(--border)] bg-white p-10 text-center text-[var(--muted)]">
            Nenhuma oportunidade neste status.
          </div>
        ) : current.map((item) => <HistoryOpportunityCard key={item.id} opportunity={item} />)}
      </section>
    </>
  );
}

function HistoryOpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  if (opportunity.status !== "measured") return <OpportunityCard opportunity={opportunity} />;
  return (
    <div>
      <OpportunityCard opportunity={opportunity} />
      <div className="-mt-2 rounded-b-2xl border border-t-0 border-[var(--border)] bg-emerald-50/60 px-5 py-3 text-sm">
        <span className="font-semibold text-emerald-800">Ganho mensurado: {currency(opportunity.measured_gain ?? 0)}</span>
        {opportunity.outcome_recorded_at && <span className="ml-3 text-[var(--muted)]">registrado em {new Date(opportunity.outcome_recorded_at).toLocaleString("pt-BR")}</span>}
      </div>
    </div>
  );
}

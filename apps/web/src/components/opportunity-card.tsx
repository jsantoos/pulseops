import Link from "next/link";

import { currency, percentage } from "@/lib/format";
import {
  categoryLabel,
  opportunityTitle,
  priorityLevel,
  severityLabel,
  statusLabel,
} from "@/lib/opportunity-presentation";
import type { Opportunity } from "@/lib/schemas";

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const critical = opportunity.severity === "critical";
  const priority = priorityLevel(opportunity.score);

  return (
    <article className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${critical ? "bg-[var(--critical-soft)] text-[var(--critical)]" : "bg-[var(--high-soft)] text-[var(--high)]"}`}>
              Severidade {severityLabel(opportunity.severity)}
            </span>
            <span className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">{categoryLabel(opportunity.category)}</span>
            <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-medium text-[var(--accent)]">{statusLabel(opportunity.status)}</span>
          </div>
          <h2 className="text-lg font-semibold tracking-tight">{opportunityTitle(opportunity)}</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Prioridade <strong className="font-semibold text-[var(--foreground)]">{priority.label}</strong> ({opportunity.score.toFixed(2)}) · Confiança da evidência {percentage(opportunity.confidence)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Potencial financeiro</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{currency(opportunity.estimated_gain)}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">estimativa, não receita garantida</p>
        </div>
      </div>
      <div className="mt-5 flex items-center justify-between border-t border-[var(--border)] pt-4">
        <span className="text-sm text-[var(--muted)]">{opportunity.recommended_actions.length} ações recomendadas</span>
        <Link href={`/opportunities/${opportunity.id}`} className="button-primary rounded-lg px-4 py-2 text-sm font-semibold hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2">Ver análise</Link>
      </div>
    </article>
  );
}

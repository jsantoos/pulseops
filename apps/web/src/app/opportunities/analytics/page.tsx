"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { getOpportunityAnalytics } from "@/lib/api";
import { currency, percentage } from "@/lib/format";
import { categoryLabel } from "@/lib/opportunity-presentation";

export default function OpportunityAnalyticsPage() {
  const query = useQuery({ queryKey: ["opportunity-analytics"], queryFn: getOpportunityAnalytics });
  if (query.isPending) return <main className="mx-auto max-w-6xl px-6 py-10">Carregando analytics…</main>;
  if (query.isError) return <main className="mx-auto max-w-6xl px-6 py-10 text-red-700">{query.error.message}</main>;
  const data = query.data;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link href="/" className="text-sm text-[var(--accent)]">← Voltar para oportunidades</Link>
      <div className="mt-5 flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">OIE · Measure</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Analytics de oportunidades</h1>
        <p className="mt-3 text-[var(--muted)]">Acompanhe adoção, mensuração e resultado financeiro das oportunidades identificadas pelo OIE. Ganho mensurado é resultado registrado e não prova causalidade da recomendação.</p>
        </div>
        <Link href="/opportunities/evolution" className="button-primary rounded-xl px-4 py-3 text-sm font-semibold">Ver evolução operacional</Link>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-4">
        <Metric label="Identificadas" value={String(data.total_opportunities)} helper={`${data.open_opportunities} abertas`} />
        <Metric label="Taxa de adoção" value={percentage(data.adoption_rate)} helper={`${data.adopted_opportunities} recomendações aceitas`} />
        <Metric label="Taxa de sucesso" value={percentage(data.success_rate)} helper={`${data.successful_opportunities} com ganho positivo entre as mensuradas`} />
        <Metric label="Mensuradas" value={String(data.measured_opportunities)} helper={`${data.dismissed_opportunities} descartadas`} />
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-3">
        <Metric label="Potencial identificado" value={currency(data.potential_identified)} helper="Estimativa associada às oportunidades atuais." />
        <Metric label="Ganho mensurado" value={currency(data.measured_gain)} helper="Valor observado informado nas oportunidades mensuradas." />
        <Metric label="Realização do potencial" value={percentage(data.realization_rate)} helper={`Comparação com ${currency(data.measured_potential)} de potencial das oportunidades já mensuradas.`} />
      </section>

      <Breakdown title="Por categoria" rows={data.by_category.map((row) => ({ ...row, label: categoryLabel(row.key) }))} />
      <Breakdown title="Por equipamento" rows={data.by_equipment.map((row) => ({ ...row, label: row.key }))} />
    </main>
  );
}

function Metric({ label, value, helper }: { label: string; value: string; helper: string }) {
  return <div className="rounded-2xl border border-[var(--border)] bg-white p-5"><p className="text-sm text-[var(--muted)]">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p><p className="mt-2 text-xs leading-5 text-[var(--muted)]">{helper}</p></div>;
}

function Breakdown({ title, rows }: { title: string; rows: Array<{ key: string; label: string; opportunities: number; measured: number; successes: number; potential_identified: number; measured_gain: number; success_rate: number; realization_rate: number }> }) {
  return (
    <section className="mt-8 overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
      <div className="p-5"><h2 className="text-xl font-semibold">{title}</h2></div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-[var(--muted)]"><tr><Th>Grupo</Th><Th>Identificadas</Th><Th>Mensuradas</Th><Th>Com sucesso</Th><Th>Potencial</Th><Th>Ganho mensurado</Th><Th>Taxa de sucesso</Th><Th>Realização</Th></tr></thead>
          <tbody>{rows.map((row) => <tr key={row.key} className="border-t border-[var(--border)]"><Td strong>{row.label}</Td><Td>{row.opportunities}</Td><Td>{row.measured}</Td><Td>{row.successes}</Td><Td>{currency(row.potential_identified)}</Td><Td>{currency(row.measured_gain)}</Td><Td>{percentage(row.success_rate)}</Td><Td>{percentage(row.realization_rate)}</Td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
function Th({ children }: { children: React.ReactNode }) { return <th className="px-4 py-3 font-medium">{children}</th>; }
function Td({ children, strong = false }: { children: React.ReactNode; strong?: boolean }) { return <td className={`px-4 py-4 ${strong ? "font-semibold" : ""}`}>{children}</td>; }

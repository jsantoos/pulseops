"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { useAuth } from "@/app/auth-provider";
import { getExecutiveSummary } from "@/lib/api";
import { currency, percentage } from "@/lib/format";
import type { ExecutiveSummary } from "@/lib/schemas";

const stateLabels: Record<string, string> = {
  improving: "Melhorando",
  worsening: "Piorando",
  mixed: "Atenção",
  stable: "Estável",
  insufficient_data: "Dados insuficientes",
};

const statusLabels: Record<string, string> = {
  open: "Aberta",
  accepted: "Aceita",
  measured: "Mensurada",
  dismissed: "Descartada",
};

export default function ExecutivePage() {
  const { activeMembership } = useAuth();
  const query = useQuery({
    queryKey: ["executive-summary", activeMembership?.organization_id],
    queryFn: getExecutiveSummary,
    enabled: Boolean(activeMembership),
  });

  if (query.isPending) return <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8">Carregando visão executiva…</main>;
  if (query.isError) return <main className="mx-auto max-w-7xl px-5 py-8 text-red-700 lg:px-8">{query.error.message}</main>;

  const data = query.data;
  const signals = buildSignals(data);

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">PulseOps · M9 · Executive Intelligence</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight lg:text-4xl">Visão executiva</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">Uma leitura consolidada de oportunidade, evolução operacional, decisões e resultados observados. Potencial é estimativa; ganho mensurado é valor registrado e não implica causalidade.</p>
        </div>
        <Freshness data={data} />
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Potencial operacional monitorado" value={currency(data.opportunities.potential_identified)} detail={`${data.opportunities.open} abertas · ${data.opportunities.in_follow_up + data.opportunities.measured} decididas/monitoradas`} />
        <Metric label="Ganho mensurado" value={currency(data.opportunities.measured_gain)} detail={`${percentage(data.opportunities.realization_rate)} do potencial associado às mensuradas`} />
        <Metric label="Taxa de adoção" value={percentage(data.opportunities.adoption_rate)} detail={`${data.opportunities.in_follow_up} em acompanhamento · ${data.opportunities.measured} mensuradas`} />
        <Metric label="Valor recuperado no-show" value={currency(data.no_show.measured_recovered_value)} detail={`${data.no_show.measured_outcomes} desfechos medidos`} />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_1fr]">
        <Panel title="Resumo executivo" subtitle="Principais mudanças desde a análise anterior.">
          <div className="space-y-3">
            {signals.map((signal) => <Signal key={signal.key} signal={signal} />)}
          </div>
          <ComparisonTable data={data} />
        </Panel>

        <Panel title="Decisões e evolução" subtitle="O que já passou por decisão e como evoluiu depois.">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <SmallMetric label="Com dados pós-decisão" value={String(data.decisions.observed_after_decision)} />
            <SmallMetric label="Melhorando" value={String(data.decisions.improving_after_decision)} />
            <SmallMetric label="Piorando" value={String(data.decisions.worsening_after_decision)} />
            <SmallMetric label="Estáveis" value={String(data.decisions.stable_after_decision)} />
            <SmallMetric label="Aguardando dados" value={String(data.decisions.awaiting_new_data)} />
            <SmallMetric label="Taxa de sucesso medida" value={percentage(data.opportunities.success_rate)} />
          </div>
          <DecisionTable rows={data.decision_rows} />
          <Link href="/opportunities/evolution" className="mt-5 inline-block text-sm font-semibold text-[var(--accent)]">Abrir evolução completa →</Link>
        </Panel>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-3">
        <Panel title="No-show · IA aplicada" subtitle="Predições, ações e resultados do fluxo individual.">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-2">
            <SmallMetric label="Predições ativas" value={String(data.no_show.active_predictions)} />
            <SmallMetric label="Ações recomendadas" value={String(data.no_show.recommended_actions)} />
            <SmallMetric label="Valor líquido esperado" value={currency(data.no_show.expected_net_value)} />
            <SmallMetric label="Intervenções executadas" value={String(data.no_show.executed_actions)} />
            <SmallMetric label="Comparecimento medido" value={percentage(data.no_show.attendance_rate)} />
            <SmallMetric label="No-show medido" value={percentage(data.no_show.no_show_rate)} />
          </div>
          <Link href="/predict" className="mt-5 mr-5 inline-block text-sm font-semibold text-[var(--accent)]">Abrir predições →</Link>
          <Link href="/measure" className="mt-5 inline-block text-sm font-semibold text-[var(--accent)]">Abrir resultados →</Link>
        </Panel>

        <Panel title="Governança do modelo" subtitle="Último modelo selecionado para risco de no-show.">
          {data.model.available ? <div className="grid grid-cols-2 gap-3">
            <SmallMetric label="ROC-AUC" value={metricNumber(data.model.roc_auc)} />
            <SmallMetric label="PR-AUC" value={metricNumber(data.model.pr_auc)} />
            <SmallMetric label="Lift @ 10%" value={metricNumber(data.model.lift_at_10pct, "×")} />
            <SmallMetric label="Brier score" value={metricNumber(data.model.brier_score)} />
            <div className="col-span-2 rounded-xl bg-slate-50 p-3 text-xs text-[var(--muted)]">
              <div><strong className="text-[var(--foreground)]">Versão:</strong> {data.model.model_version ?? "—"}</div>
              <div className="mt-1"><strong className="text-[var(--foreground)]">Feature set:</strong> {data.model.feature_set_version ?? "—"}</div>
            </div>
          </div> : <Empty>Ainda não há modelo treinado.</Empty>}
        </Panel>

        <Panel title="Prioridades agora" subtitle={data.opportunities.open > 0 ? "Oportunidades abertas ordenadas pelo score do OIE." : "Sem decisões pendentes; mostramos os itens monitorados que ainda exigem atenção."}>
          {data.top_priorities.length === 0 ? <Empty>Nenhuma prioridade operacional crítica no momento.</Empty> : <div className="space-y-3">
            {data.top_priorities.slice(0, 4).map((item) => (
              <Link key={item.opportunity_id} href={`/opportunities/${item.opportunity_id}`} className="block rounded-xl border border-[var(--border)] p-3 hover:bg-slate-50">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold">{item.title}</div>
                    <div className="mt-1 text-xs text-[var(--muted)]">{item.equipment_id?.toUpperCase() ?? "Operação"} · {statusLabels[item.status] ?? item.status} · score {item.score.toFixed(0)}</div>
                  </div>
                  <div className="shrink-0 text-sm font-semibold">{currency(item.estimated_gain)}</div>
                </div>
              </Link>
            ))}
          </div>}
          <Link href="/" className="mt-5 inline-block text-sm font-semibold text-[var(--accent)]">Abrir oportunidades →</Link>
        </Panel>
      </section>

      <Panel className="mt-6" title="Operação por equipamento" subtitle="Estado atual das séries de capacidade e cancelamentos/no-show.">
        {data.equipments.length === 0 ? <Empty>Nenhum histórico operacional disponível.</Empty> : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {data.equipments.map((item) => <EquipmentRow key={item.equipment_id} item={item} />)}
          </div>
        )}
        <Link href="/opportunities/evolution" className="mt-5 inline-block text-sm font-semibold text-[var(--accent)]">Abrir evolução operacional →</Link>
      </Panel>

      <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50/50 p-4 text-sm text-slate-700"><strong>Leitura executiva:</strong> use esta tela para priorizar atenção e acompanhar evolução. Para decisões operacionais, abra a análise correspondente; para investigação, consulte Analytics OIE, Evolução e Resultados.</div>
    </main>
  );
}

function Freshness({ data }: { data: ExecutiveSummary }) {
  return <div className="rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-right text-xs text-[var(--muted)]"><div className="font-semibold text-[var(--foreground)]">Dados mais recentes</div><div className="mt-1">{data.latest_dataset_at ? new Date(data.latest_dataset_at).toLocaleString("pt-BR") : "Nenhum dataset"}</div><div className="mt-1">Status: {data.latest_dataset_status ?? "—"}</div></div>;
}

function buildSignals(data: ExecutiveSummary) {
  const grouped = new Map<string, ExecutiveSummary["comparisons"]>();
  for (const row of data.comparisons.filter((item) => item.equipment_id)) {
    const key = row.equipment_id ?? "";
    grouped.set(key, [...(grouped.get(key) ?? []), row]);
  }

  const signals = [...grouped.entries()].map(([equipmentId, rows]) => {
    const worsening = rows.filter((row) => row.trend === "worsening");
    const improving = rows.filter((row) => row.trend === "improving");
    const tone = worsening.length > 0 ? "bad" : improving.length > 0 ? "good" : "neutral";
    const state = worsening.length > 0 ? "piorou" : improving.length > 0 ? "melhorou" : "ficou estável";
    const detail = rows.map((row) => `${comparisonShortLabel(row)} ${formatDelta(row)}`).join(" · ");
    return { key: equipmentId, tone, title: `${equipmentId.toUpperCase()} ${state}`, detail };
  });

  signals.sort((a, b) => (a.tone === "bad" ? -1 : b.tone === "bad" ? 1 : 0));
  if (data.opportunities.open === 0) {
    signals.push({ key: "workflow", tone: "info", title: "Sem novas oportunidades abertas", detail: "Todas as oportunidades operacionais atuais já receberam decisão gerencial." });
  }
  return signals.slice(0, 4);
}

function Signal({ signal }: { signal: ReturnType<typeof buildSignals>[number] }) {
  const classes = signal.tone === "good"
    ? "border-emerald-200 bg-emerald-50/70 text-emerald-900"
    : signal.tone === "bad"
      ? "border-red-200 bg-red-50/70 text-red-900"
      : signal.tone === "info"
        ? "border-blue-200 bg-blue-50/70 text-blue-900"
        : "border-slate-200 bg-slate-50 text-slate-800";
  const icon = signal.tone === "good" ? "↗" : signal.tone === "bad" ? "↘" : "i";
  return <div className={`flex gap-3 rounded-xl border p-3 ${classes}`}><span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/70 text-lg font-semibold">{icon}</span><div><div className="text-sm font-semibold">{signal.title}</div><div className="mt-1 text-xs leading-5 opacity-80">{signal.detail}</div></div></div>;
}

function ComparisonTable({ data }: { data: ExecutiveSummary }) {
  if (!data.comparisons.length) return <div className="mt-5"><Empty>Ainda não há dois períodos comparáveis.</Empty></div>;
  return <div className="mt-6 overflow-x-auto"><div className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">Comparativo · últimos 2 períodos</div><table className="min-w-full text-left text-xs"><thead><tr className="border-b border-[var(--border)] text-[var(--muted)]"><Th>Indicador</Th><Th>Atual</Th><Th>Anterior</Th><Th>Variação</Th></tr></thead><tbody>{data.comparisons.map((row) => <tr key={row.key} className="border-b border-[var(--border)] last:border-0"><Td strong>{comparisonLabel(row)}</Td><Td>{formatMetric(row.current, row.unit)}</Td><Td>{formatMetric(row.previous, row.unit)}</Td><Td><span className={row.trend === "improving" ? "font-semibold text-emerald-700" : row.trend === "worsening" ? "font-semibold text-red-700" : "text-[var(--muted)]"}>{row.delta > 0 ? "↑" : row.delta < 0 ? "↓" : "→"} {formatDelta(row)}</span></Td></tr>)}</tbody></table><p className="mt-3 text-[11px] text-[var(--muted)]">Variações calculadas a partir dos dois snapshots operacionais mais recentes disponíveis.</p></div>;
}

function DecisionTable({ rows }: { rows: ExecutiveSummary["decision_rows"] }) {
  const visible = rows.filter((row) => row.snapshots_after_decision > 0).slice(0, 6);
  if (!visible.length) return <div className="mt-5"><Empty>As decisões atuais ainda aguardam novos dados operacionais.</Empty></div>;
  return <div className="mt-5 overflow-x-auto"><table className="min-w-full text-left text-xs"><thead><tr className="border-b border-[var(--border)] text-[var(--muted)]"><Th>Oportunidade</Th><Th>Status</Th><Th>Último pós-decisão</Th><Th>Variação</Th></tr></thead><tbody>{visible.map((row) => <tr key={row.opportunity_id} className="border-b border-[var(--border)] last:border-0"><Td strong>{row.equipment_id?.toUpperCase() ?? "Operação"} · {row.category === "capacity" ? "capacidade" : "cancelamento"}</Td><Td><span className="rounded-full bg-slate-100 px-2 py-1">{statusLabels[row.status] ?? row.status}</span></Td><Td>{row.current == null ? "—" : formatMetric(row.current, row.primary_metric_unit ?? "number")}</Td><Td><span className={row.trend === "improving" ? "font-semibold text-emerald-700" : row.trend === "worsening" ? "font-semibold text-red-700" : "text-[var(--muted)]"}>{row.delta == null ? "—" : `${row.delta > 0 ? "+" : ""}${formatMetric(row.delta, row.primary_metric_unit ?? "number", true)}`}</span></Td></tr>)}</tbody></table></div>;
}

function comparisonLabel(row: ExecutiveSummary["comparisons"][number]) { return row.equipment_id ? `${row.equipment_id.toUpperCase()} · ${row.label}` : row.label; }
function comparisonShortLabel(row: ExecutiveSummary["comparisons"][number]) { return row.category === "capacity" ? "utilização" : row.category === "cancellation" ? "perda de agenda" : row.label.toLowerCase(); }
function formatDelta(row: ExecutiveSummary["comparisons"][number]) { const prefix = row.delta > 0 ? "+" : ""; return `${prefix}${formatMetric(row.delta, row.unit, true)}`; }
function formatMetric(value: number, unit: string, compactDelta = false) {
  if (unit === "currency") return currency(value);
  if (unit === "percent") return compactDelta ? `${(value * 100).toFixed(1)} p.p.` : percentage(value);
  if (unit === "minutes") return `${Math.round(value)} min`;
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value);
}
function Panel({ title, subtitle, children, className = "" }: { title: string; subtitle: string; children: React.ReactNode; className?: string }) { return <section className={`${className} rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm`}><h2 className="text-lg font-semibold">{title}</h2><p className="mt-1 text-xs leading-5 text-[var(--muted)]">{subtitle}</p><div className="mt-5">{children}</div></section>; }
function Metric({ label, value, detail }: { label: string; value: string; detail: string }) { return <div className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm"><div className="text-xs text-[var(--muted)]">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div><div className="mt-2 text-xs leading-5 text-[var(--muted)]">{detail}</div></div>; }
function SmallMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-slate-50 p-3"><div className="text-xs text-[var(--muted)]">{label}</div><div className="mt-1 text-lg font-semibold">{value}</div></div>; }
function Empty({ children }: { children: React.ReactNode }) { return <div className="rounded-xl bg-slate-50 p-5 text-sm text-[var(--muted)]">{children}</div>; }
function EquipmentRow({ item }: { item: ExecutiveSummary["equipments"][number] }) { return <div className="rounded-xl border border-[var(--border)] p-4"><div className="flex items-center justify-between gap-4"><div><div className="font-semibold uppercase">{item.equipment_id}</div><div className="mt-1 text-xs text-[var(--muted)]">Potencial atual {currency(item.potential)}</div></div><span className={badgeClass(item.state)}>{stateLabels[item.state]}</span></div><div className="mt-3 grid grid-cols-2 gap-3 text-sm"><div><span className="text-xs text-[var(--muted)]">Utilização</span><div className="font-semibold">{item.utilization == null ? "—" : percentage(item.utilization)}</div></div><div><span className="text-xs text-[var(--muted)]">Perda de agenda</span><div className="font-semibold">{item.loss_rate == null ? "—" : percentage(item.loss_rate)}</div></div></div></div>; }
function badgeClass(state: string) { if (state === "improving") return "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"; if (state === "worsening") return "rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700"; if (state === "mixed") return "rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800"; return "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"; }
function metricNumber(value: number | null | undefined, suffix = "") { return value == null ? "—" : `${value.toFixed(3)}${suffix}`; }
function Th({ children }: { children: React.ReactNode }) { return <th className="px-2 py-2 font-medium first:pl-0">{children}</th>; }
function Td({ children, strong = false }: { children: React.ReactNode; strong?: boolean }) { return <td className={`px-2 py-2.5 first:pl-0 ${strong ? "font-medium" : ""}`}>{children}</td>; }

"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { getOpportunityTemporal } from "@/lib/api";
import { currency, durationMinutes, numberPtBr, percentage } from "@/lib/format";
import { categoryLabel } from "@/lib/opportunity-presentation";
import type { OpportunityDecisionImpact, OpportunityTemporalSeries } from "@/lib/schemas";

const trendLabels = {
  improving: "Melhorando",
  worsening: "Piorando",
  stable: "Estável",
  insufficient_data: "Dados insuficientes",
} as const;

export default function OpportunityEvolutionPage() {
  const query = useQuery({
    queryKey: ["opportunity-temporal"],
    queryFn: getOpportunityTemporal,
  });

  if (query.isPending) {
    return <main className="mx-auto max-w-6xl px-6 py-10">Carregando evolução operacional…</main>;
  }
  if (query.isError) {
    return <main className="mx-auto max-w-6xl px-6 py-10 text-red-700">{query.error.message}</main>;
  }

  const data = query.data;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-3xl">
          <Link href="/opportunities/analytics" className="text-sm text-[var(--accent)]">← Voltar para Analytics OIE</Link>
          <p className="mt-6 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">OIE · M8 · Temporal Intelligence</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Evolução operacional</h1>
          <p className="mt-3 text-[var(--muted)]">Compare como capacidade, cancelamentos e perdas evoluem entre novas análises. Cada ponto vem de um snapshot imutável gerado a partir de um dataset analisado.</p>
        </div>
        <Link href="/" className="rounded-xl border border-[var(--border)] bg-white px-4 py-3 text-sm font-semibold hover:bg-slate-50">Ver oportunidades atuais</Link>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Metric label="Equipamentos" value={String(data.equipment_count)} helper="Recursos com histórico operacional." />
        <Metric label="Séries acompanhadas" value={String(data.series_count)} helper="Capacidade e cancelamento/no-show." />
        <Metric label="Melhorando" value={String(data.improving)} helper="Indicador principal evoluiu favoravelmente." />
        <Metric label="Piorando" value={String(data.worsening)} helper="Indicador principal exige atenção." />
        <Metric label="Estáveis" value={String(data.stable)} helper={`${data.insufficient_data} com dados insuficientes.`} />
      </section>

      {data.equipments.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-dashed border-[var(--border)] bg-white p-10 text-center text-[var(--muted)]">Ainda não há snapshots operacionais suficientes para montar a visão temporal.</div>
      ) : (
        <section className="mt-8 space-y-6">
          {data.equipments.map((equipment) => (
            <article key={equipment.equipment_id} className="overflow-hidden rounded-3xl border border-[var(--border)] bg-white shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] px-6 py-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">Equipamento</p>
                  <h2 className="mt-1 text-2xl font-semibold uppercase">{equipment.equipment_id}</h2>
                </div>
                <div className="flex flex-wrap gap-2 text-sm">
                  <Badge tone="good">{equipment.improving} melhorando</Badge>
                  <Badge tone="bad">{equipment.worsening} piorando</Badge>
                  <Badge tone="neutral">{equipment.stable} estáveis</Badge>
                </div>
              </div>

              <div className="grid gap-5 p-6 lg:grid-cols-2">
                {equipment.series.map((series) => <SeriesCard key={series.opportunity_id} series={series} />)}
              </div>
            </article>
          ))}
        </section>
      )}

      <div className="mt-8 rounded-2xl border border-blue-200 bg-blue-50 p-5 text-sm leading-6 text-blue-950">
        <strong>Como interpretar:</strong> a evolução mostra associação temporal entre análises. Se uma recomendação foi aceita no intervalo, ela aparece no histórico da oportunidade, mas a mudança posterior não é tratada automaticamente como efeito causal da recomendação.
      </div>
    </main>
  );
}

function SeriesCard({ series }: { series: OpportunityTemporalSeries }) {
  const primaryKey = series.category === "capacity" ? "utilization" : "loss_rate";
  const primary = series.metrics.find((metric) => metric.key === primaryKey);
  const potential = series.metrics.find((metric) => metric.key === "estimated_gain");
  const primaryValues = series.series
    .map((point) => pointValue(point, primaryKey))
    .filter((value): value is number => value !== null);
  const potentialValues = series.series.map((point) => point.estimated_gain);

  return (
    <div className="rounded-2xl border border-[var(--border)] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">{categoryLabel(series.category)}</p>
          <h3 className="mt-1 text-lg font-semibold">{series.title}</h3>
          <p className="mt-1 text-xs text-[var(--muted)]">{series.snapshot_count} snapshots · status {series.status}</p>
        </div>
        <TrendBadge trend={series.trend} />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {primary && (
          <MetricPanel
            label={primary.label}
            current={formatMetric(primary.current, primary.unit)}
            initial={`Inicial ${formatMetric(primary.initial, primary.unit)}`}
            delta={`Δ ${formatDelta(primary.delta, primary.unit)}`}
            values={primaryValues}
          />
        )}
        {potential && (
          <MetricPanel
            label="Potencial financeiro"
            current={currency(potential.current)}
            initial={`Inicial ${currency(potential.initial)}`}
            delta={`Δ ${currency(potential.delta)}`}
            values={potentialValues}
          />
        )}
      </div>

      <DecisionImpactPanel impact={series.decision_impact} />

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-xs">
          <thead className="text-[var(--muted)]">
            <tr><Th>Análise</Th><Th>Data</Th><Th>Contexto</Th><Th>{primary?.label ?? "Indicador"}</Th><Th>Potencial</Th><Th>Prioridade</Th></tr>
          </thead>
          <tbody>
            {series.series.map((point, index) => {
              const value = pointValue(point, primaryKey);
              return (
                <tr key={point.snapshot_id} className="border-t border-[var(--border)]">
                  <Td>#{index + 1}</Td>
                  <Td>{new Date(point.observed_at).toLocaleDateString("pt-BR")}</Td>
                  <Td><SnapshotContext pointDate={point.observed_at} impact={series.decision_impact} /></Td>
                  <Td>{value === null ? "—" : formatMetric(value, primary?.unit ?? "count")}</Td>
                  <Td>{currency(point.estimated_gain)}</Td>
                  <Td>{numberPtBr(point.score, 1)}</Td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] pt-4">
        <div className="text-xs text-[var(--muted)]">
          {series.decision_impact.state === "post_decision_observed"
            ? `${series.decision_impact.snapshots_after_decision} análise(s) após a decisão`
            : series.decided_at
              ? "Aguardando nova análise após a decisão"
              : "Sem decisão gerencial registrada"}
        </div>
        <Link href={`/opportunities/${series.opportunity_id}`} className="font-semibold text-[var(--accent)]">Abrir análise →</Link>
      </div>
    </div>
  );
}

function DecisionImpactPanel({ impact }: { impact: OpportunityDecisionImpact }) {
  if (impact.state === "not_decided") {
    return (
      <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-[var(--muted)]">
        <strong className="text-slate-900">Decisão × evolução:</strong> ainda não há decisão gerencial registrada para esta oportunidade.
      </div>
    );
  }

  if (impact.state === "dismissed") {
    return (
      <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
        <div className="font-semibold">Recomendação descartada</div>
        <p className="mt-1 text-[var(--muted)]">A decisão permanece na linha do tempo para comparação histórica; mudanças posteriores não representam uma intervenção aceita.</p>
        {impact.decision_note && <p className="mt-2 rounded-lg bg-white p-3 text-xs">Decisão: {impact.decision_note}</p>}
      </div>
    );
  }

  const hasPostDecision = impact.state === "post_decision_observed";
  const hasMeasuredGain = impact.measured_gain !== null && impact.measured_gain !== undefined;

  return (
    <div className={`mt-5 rounded-xl border p-4 ${hasPostDecision ? "border-emerald-200 bg-emerald-50/60" : "border-amber-200 bg-amber-50/70"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">Decisão → evolução → resultado</p>
          <p className="mt-1 font-semibold">
            {hasPostDecision ? "Há novas análises após a decisão" : "Decisão registrada · aguardando novo período"}
          </p>
          {impact.decided_at && <p className="mt-1 text-xs text-[var(--muted)]">Decidida em {new Date(impact.decided_at).toLocaleString("pt-BR")}</p>}
        </div>
        <Badge tone={hasPostDecision ? "good" : "neutral"}>
          {impact.snapshots_after_decision} snapshot(s) após decisão
        </Badge>
      </div>

      {impact.decision_note && <p className="mt-3 rounded-lg bg-white/80 p-3 text-xs">Decisão: {impact.decision_note}</p>}

      {hasPostDecision && impact.primary_metric_label && impact.baseline_before_decision !== null && impact.baseline_before_decision !== undefined && impact.current_after_decision !== null && impact.current_after_decision !== undefined ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <SmallMetric label="Na decisão" value={formatMetric(impact.baseline_before_decision, impact.primary_metric_unit ?? "count")} />
          <SmallMetric label="Último pós-decisão" value={formatMetric(impact.current_after_decision, impact.primary_metric_unit ?? "count")} />
          <SmallMetric label="Variação observada" value={formatDelta(impact.delta_after_decision ?? 0, impact.primary_metric_unit ?? "count")} />
        </div>
      ) : null}

      {hasMeasuredGain && (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <SmallMetric label="Ganho mensurado" value={currency(impact.measured_gain ?? 0)} />
          <SmallMetric label="Potencial na mensuração" value={impact.potential_at_outcome == null ? "—" : currency(impact.potential_at_outcome)} />
          <SmallMetric label="Realização observada" value={impact.realization_rate == null ? "—" : percentage(impact.realization_rate)} />
        </div>
      )}

      {impact.outcome_notes && <p className="mt-3 text-xs text-[var(--muted)]">Resultado registrado: {impact.outcome_notes}</p>}
      <p className="mt-3 text-xs leading-5 text-[var(--muted)]">A comparação é temporal e observacional. O PulseOps não atribui causalidade automaticamente à decisão.</p>
    </div>
  );
}

function SnapshotContext({ pointDate, impact }: { pointDate: string; impact: OpportunityDecisionImpact }) {
  if (!impact.decided_at) return <span className="text-[var(--muted)]">Pré-decisão</span>;
  const point = new Date(pointDate).getTime();
  const decided = new Date(impact.decided_at).getTime();
  if (point > decided) return <span className="font-semibold text-emerald-700">Após decisão</span>;
  return <span className="text-[var(--muted)]">Antes da decisão</span>;
}

function SmallMetric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-white/80 p-3"><p className="text-[10px] uppercase tracking-wide text-[var(--muted)]">{label}</p><p className="mt-1 font-semibold">{value}</p></div>;
}

function pointValue(point: OpportunityTemporalSeries["series"][number], key: string): number | null {
  if (key === "estimated_gain") return point.estimated_gain;
  const value = point.evidence[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatMetric(value: number, unit: string): string {
  if (unit === "percent") return percentage(value);
  if (unit === "minutes") return durationMinutes(value);
  if (unit === "currency") return currency(value);
  if (unit === "currency_per_minute") return `${currency(value)}/min`;
  return numberPtBr(value, 1);
}

function formatDelta(value: number, unit: string): string {
  const prefix = value > 0 ? "+" : value < 0 ? "−" : "";
  const absolute = Math.abs(value);
  if (unit === "percent") return `${prefix}${numberPtBr(absolute * 100, 1)} p.p.`;
  if (unit === "minutes") return `${prefix}${durationMinutes(absolute)}`;
  if (unit === "currency") return `${prefix}${currency(absolute)}`;
  return `${prefix}${numberPtBr(absolute, 1)}`;
}

function MetricPanel({ label, current, initial, delta, values }: { label: string; current: string; initial: string; delta: string; values: number[] }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-xl font-semibold">{current}</p>
      <p className="mt-1 text-xs text-[var(--muted)]">{initial} · {delta}</p>
      <Sparkline values={values} />
    </div>
  );
}

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return <div className="mt-3 h-10 text-xs text-[var(--muted)]">Aguardando mais análises</div>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 180;
  const height = 40;
  const points = values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * width;
    const y = height - ((value - min) / range) * (height - 6) - 3;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mt-3 h-10 w-full text-[var(--accent)]" role="img" aria-label="Evolução entre snapshots">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TrendBadge({ trend }: { trend: OpportunityTemporalSeries["trend"] }) {
  const tone = trend === "improving" ? "good" : trend === "worsening" ? "bad" : "neutral";
  return <Badge tone={tone}>{trendLabels[trend]}</Badge>;
}

function Badge({ children, tone }: { children: React.ReactNode; tone: "good" | "bad" | "neutral" }) {
  const className = tone === "good" ? "bg-emerald-50 text-emerald-800" : tone === "bad" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-700";
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${className}`}>{children}</span>;
}

function Metric({ label, value, helper }: { label: string; value: string; helper: string }) {
  return <div className="rounded-2xl border border-[var(--border)] bg-white p-5"><p className="text-sm text-[var(--muted)]">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p><p className="mt-2 text-xs leading-5 text-[var(--muted)]">{helper}</p></div>;
}

function Th({ children }: { children: React.ReactNode }) { return <th className="px-3 py-2 font-medium">{children}</th>; }
function Td({ children }: { children: React.ReactNode }) { return <td className="px-3 py-3">{children}</td>; }

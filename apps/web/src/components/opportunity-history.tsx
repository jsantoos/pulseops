"use client";

import type { OpportunityHistory, OpportunityHistoryMetric } from "@/lib/schemas";
import { currency, percentage } from "@/lib/format";

const trendLabels = {
  improving: "Melhorando",
  worsening: "Piorando",
  stable: "Estável",
  insufficient_data: "Histórico insuficiente",
} as const;

function trendClass(trend: OpportunityHistoryMetric["trend"] | OpportunityHistory["trend"]): string {
  if (trend === "improving") return "bg-emerald-50 text-emerald-800";
  if (trend === "worsening") return "bg-red-50 text-red-800";
  if (trend === "stable") return "bg-slate-100 text-slate-700";
  return "bg-amber-50 text-amber-800";
}

function formatMetricValue(value: number, unit: string): string {
  if (unit === "percent") return percentage(value);
  if (unit === "currency") return currency(value);
  if (unit === "currency_per_minute") return `${currency(value)} / min`;
  if (unit === "minutes") {
    const hours = value / 60;
    return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(hours)} h`;
  }
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value);
}

function formatDelta(metric: OpportunityHistoryMetric): string {
  if (metric.unit === "percent") {
    const points = metric.delta * 100;
    return `${points >= 0 ? "+" : ""}${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(points)} p.p.`;
  }
  const formatted = formatMetricValue(Math.abs(metric.delta), metric.unit);
  return `${metric.delta >= 0 ? "+" : "−"}${formatted}`;
}

function pointMetricValue(point: OpportunityHistory["series"][number], key: string): number | null {
  if (key === "estimated_gain") return point.estimated_gain;
  const value = point.evidence[key];
  return typeof value === "number" ? value : null;
}

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 180;
  const height = 48;
  const pad = 4;
  const points = values.map((value, index) => {
    const x = pad + (index / Math.max(values.length - 1, 1)) * (width - pad * 2);
    const y = height - pad - ((value - min) / range) * (height - pad * 2);
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mt-3 h-12 w-full" role="img" aria-label="Evolução da métrica">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {points.split(" ").map((point, index) => {
        const [cx, cy] = point.split(",");
        return <circle key={`${point}-${index}`} cx={cx} cy={cy} r="3" fill="currentColor" />;
      })}
    </svg>
  );
}

function DecisionImpactSummary({ history }: { history: OpportunityHistory }) {
  const impact = history.decision_impact;
  if (impact.state === "not_decided") return null;

  const hasPostDecision = impact.state === "post_decision_observed";
  const hasMeasuredGain = impact.measured_gain !== null && impact.measured_gain !== undefined;

  return (
    <div className={`mt-6 rounded-xl border p-5 ${impact.state === "dismissed" ? "border-slate-200 bg-slate-50" : hasPostDecision ? "border-emerald-200 bg-emerald-50/60" : "border-amber-200 bg-amber-50/70"}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">M8.4 · Decisão × evolução × resultado</p>
          <h3 className="mt-1 font-semibold">{impact.state === "dismissed" ? "Recomendação descartada" : hasPostDecision ? "Há novas análises após a decisão" : "Aguardando novo período após a decisão"}</h3>
          {impact.decided_at && <p className="mt-1 text-xs text-[var(--muted)]">Decisão registrada em {new Date(impact.decided_at).toLocaleString("pt-BR")}</p>}
        </div>
        <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold">{impact.snapshots_after_decision} pós-decisão</span>
      </div>

      {impact.decision_note && <p className="mt-3 rounded-lg bg-white/80 p-3 text-sm">Decisão: {impact.decision_note}</p>}

      {hasPostDecision && impact.primary_metric_label && impact.baseline_before_decision != null && impact.current_after_decision != null && (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <DecisionMetric label={`${impact.primary_metric_label} na decisão`} value={formatMetricValue(impact.baseline_before_decision, impact.primary_metric_unit ?? "count")} />
          <DecisionMetric label="Último valor pós-decisão" value={formatMetricValue(impact.current_after_decision, impact.primary_metric_unit ?? "count")} />
          <DecisionMetric label="Variação observada" value={formatImpactDelta(impact.delta_after_decision ?? 0, impact.primary_metric_unit ?? "count")} />
        </div>
      )}

      {hasMeasuredGain && (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <DecisionMetric label="Ganho mensurado" value={currency(impact.measured_gain ?? 0)} />
          <DecisionMetric label="Potencial na mensuração" value={impact.potential_at_outcome == null ? "—" : currency(impact.potential_at_outcome)} />
          <DecisionMetric label="Realização observada" value={impact.realization_rate == null ? "—" : percentage(impact.realization_rate)} />
        </div>
      )}

      {impact.outcome_notes && <p className="mt-3 text-sm text-[var(--muted)]">Resultado registrado: {impact.outcome_notes}</p>}
      <p className="mt-3 text-xs leading-5 text-[var(--muted)]">A relação é temporal e observacional. A evolução posterior não é tratada como prova de causalidade da recomendação.</p>
    </div>
  );
}

function DecisionMetric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-white/80 p-3"><p className="text-[10px] uppercase tracking-wide text-[var(--muted)]">{label}</p><p className="mt-1 font-semibold">{value}</p></div>;
}

function formatImpactDelta(value: number, unit: string): string {
  const prefix = value > 0 ? "+" : value < 0 ? "−" : "";
  const absolute = Math.abs(value);
  if (unit === "percent") return `${prefix}${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(absolute * 100)} p.p.`;
  return `${prefix}${formatMetricValue(absolute, unit)}`;
}

function snapshotContext(pointDate: string, decidedAt?: string | null): React.ReactNode {
  if (!decidedAt) return <span className="text-[var(--muted)]">Pré-decisão</span>;
  return new Date(pointDate).getTime() > new Date(decidedAt).getTime()
    ? <span className="font-semibold text-emerald-700">Após decisão</span>
    : <span className="text-[var(--muted)]">Antes da decisão</span>;
}

export function OpportunityHistoryPanel({ history }: { history: OpportunityHistory }) {
  const highlighted = history.metrics.filter((metric) =>
    history.category === "capacity"
      ? ["utilization", "realized_minutes", "recoverable_minutes", "estimated_gain"].includes(metric.key)
      : ["loss_rate", "no_shows", "lost_revenue", "estimated_gain"].includes(metric.key),
  );

  return (
    <section className="mt-8 rounded-2xl border border-[var(--border)] bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">M8 · Histórico operacional</p>
          <h2 className="mt-2 text-xl font-semibold">Evolução entre análises</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--muted)]">
            Cada ponto representa uma análise de um dataset diferente para a mesma oportunidade operacional. O histórico é preservado; o card principal mostra apenas o estado mais recente.
          </p>
        </div>
        <div className="text-right">
          <span className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${trendClass(history.trend)}`}>
            {trendLabels[history.trend]}
          </span>
          <p className="mt-2 text-xs text-[var(--muted)]">{history.snapshot_count} snapshots</p>
        </div>
      </div>

      {history.snapshot_count < 2 ? (
        <div className="mt-6 rounded-xl bg-slate-50 p-5 text-sm text-[var(--muted)]">
          Ainda há apenas uma fotografia operacional. Importe e analise um novo período para habilitar comparação temporal.
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {highlighted.map((metric) => {
              const values = history.series
                .map((point) => pointMetricValue(point, metric.key))
                .filter((value): value is number => value !== null);
              return (
                <div key={metric.key} className="rounded-xl bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{metric.label}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${trendClass(metric.trend)}`}>
                      {trendLabels[metric.trend]}
                    </span>
                  </div>
                  <p className="mt-2 text-xl font-semibold">{formatMetricValue(metric.current, metric.unit)}</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Inicial {formatMetricValue(metric.initial, metric.unit)} · Δ {formatDelta(metric)}
                  </p>
                  <div className={metric.trend === "worsening" ? "text-red-600" : metric.trend === "improving" ? "text-emerald-600" : "text-slate-500"}>
                    <Sparkline values={values} />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 overflow-x-auto rounded-xl border border-[var(--border)]">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-[var(--muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">Análise</th>
                  <th className="px-4 py-3 font-medium">Data</th>
                  <th className="px-4 py-3 font-medium">Contexto</th>
                  {highlighted.map((metric) => <th key={metric.key} className="px-4 py-3 font-medium">{metric.label}</th>)}
                  <th className="px-4 py-3 font-medium">Prioridade</th>
                </tr>
              </thead>
              <tbody>
                {history.series.map((point, index) => (
                  <tr key={point.snapshot_id} className="border-t border-[var(--border)]">
                    <td className="px-4 py-3 font-semibold">#{index + 1}</td>
                    <td className="px-4 py-3 text-[var(--muted)]">{new Date(point.observed_at).toLocaleString("pt-BR")}</td>
                    <td className="px-4 py-3">{snapshotContext(point.observed_at, history.decision_impact.decided_at)}</td>
                    {highlighted.map((metric) => {
                      const value = pointMetricValue(point, metric.key);
                      return <td key={metric.key} className="px-4 py-3">{value === null ? "—" : formatMetricValue(value, metric.unit)}</td>;
                    })}
                    <td className="px-4 py-3">{new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(point.score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <DecisionImpactSummary history={history} />
    </section>
  );
}

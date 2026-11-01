"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/app/auth-provider";
import { getNoShowMeasureSummary } from "@/lib/api";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const pct = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 });
const channelLabels: Record<string, string> = { whatsapp: "WhatsApp", phone: "Telefone", sms: "SMS", email: "E-mail", other: "Outro", legacy: "Legado" };

export default function MeasurePage() {
  const { activeMembership } = useAuth();
  const measure = useQuery({
    queryKey: ["no-show-measure-summary", activeMembership?.organization_id],
    queryFn: getNoShowMeasureSummary,
    enabled: Boolean(activeMembership),
  });
  const data = measure.data;

  return <main className="mx-auto max-w-6xl px-6 py-10">
    <div className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">PulseOps Measure · M7</p>
      <h1 className="mt-2 text-4xl font-semibold tracking-tight">Resultados das intervenções</h1>
      <p className="mt-3 text-[var(--muted)]">Acompanhe o ciclo completo entre recomendação, execução, desfecho observado e valor recuperado.</p>
    </div>

    {measure.isError && <div className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-800">{measure.error.message}</div>}
    {measure.isLoading && <div className="mt-8 text-[var(--muted)]">Carregando indicadores…</div>}
    {data && <>
      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <Metric label="Intervenções executadas" value={String(data.executed_actions)} />
        <Metric label="Resultados medidos" value={String(data.measured_outcomes)} />
        <Metric label="Aguardando desfecho" value={String(data.pending_outcomes)} />
      </section>
      <section className="mt-4 grid gap-4 md:grid-cols-3">
        <Metric label="Taxa de comparecimento" value={pct.format(data.attendance_rate)} detail={`${data.attended} comparecimentos medidos`} />
        <Metric label="No-show após intervenção" value={pct.format(data.no_show_rate)} detail={`${data.no_show} no-shows medidos`} />
        <Metric label="Cancelamentos" value={pct.format(data.cancellation_rate)} detail={`${data.cancelled} cancelamentos medidos`} />
      </section>
      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <Metric label="Receita realizada" value={money.format(data.realized_revenue)} />
        <Metric label="Valor recuperado medido" value={money.format(data.measured_recovered_value)} detail="Valor informado/atribuído pela operação; não é inferido automaticamente pelo ML." />
      </section>

      <section className="mt-8 overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
        <div className="border-b border-[var(--border)] p-5"><h2 className="text-xl font-semibold">Desempenho por canal</h2><p className="mt-1 text-sm text-[var(--muted)]">Resultados observados agrupados pelo canal usado na intervenção.</p></div>
        {data.by_channel.length === 0 ? <div className="p-8 text-center text-[var(--muted)]">Ainda não há intervenções registradas.</div> :
        <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-[var(--muted)]"><tr><Th>Canal</Th><Th>Intervenções</Th><Th>Medidos</Th><Th>Compareceram</Th><Th>No-show</Th><Th>Cancelaram</Th><Th>Receita</Th><Th>Recuperado</Th></tr></thead><tbody>{data.by_channel.map(row => <tr key={row.channel} className="border-t border-[var(--border)]"><Td strong>{channelLabels[row.channel] ?? row.channel}</Td><Td>{row.interventions}</Td><Td>{row.measured_outcomes}</Td><Td>{row.attended}</Td><Td>{row.no_show}</Td><Td>{row.cancelled}</Td><Td>{money.format(row.realized_revenue)}</Td><Td>{money.format(row.measured_recovered_value)}</Td></tr>)}</tbody></table></div>}
      </section>
      <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50/50 p-4 text-sm text-slate-700"><strong>Como interpretar:</strong> estes indicadores medem o que ocorreu depois das intervenções registradas. Eles ainda não provam causalidade; servem para acompanhar operação, resultado financeiro e preparar a avaliação do Learning Loop.</div>
    </>}
  </main>;
}
function Metric({label,value,detail}:{label:string;value:string;detail?:string}) { return <div className="rounded-2xl border border-[var(--border)] bg-white p-5"><div className="text-sm text-[var(--muted)]">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div>{detail && <div className="mt-2 text-xs text-[var(--muted)]">{detail}</div>}</div>; }
function Th({children}:{children:React.ReactNode}) { return <th className="whitespace-nowrap px-4 py-3 font-medium">{children}</th>; }
function Td({children,strong=false}:{children:React.ReactNode;strong?:boolean}) { return <td className={`whitespace-nowrap px-4 py-3 ${strong ? "font-semibold" : ""}`}>{children}</td>; }

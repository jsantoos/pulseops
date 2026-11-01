"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/app/auth-provider";
import { listNoShowPredictions, recordNoShowIntervention } from "@/lib/api";
import type { NoShowPrediction } from "@/lib/schemas";

const percent = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

const channelLabels: Record<string, string> = {
  whatsapp: "WhatsApp",
  phone: "Telefone",
  sms: "SMS",
  email: "E-mail",
  other: "Outro",
};
const resultLabels: Record<string, string> = {
  confirmed: "Confirmou presença",
  no_response: "Não respondeu",
  cancelled: "Solicitou cancelamento",
  rescheduled: "Solicitou reagendamento",
  unsuccessful: "Contato sem sucesso",
  other: "Outro",
};

type Channel = "whatsapp" | "phone" | "sms" | "email" | "other";
type ContactResult = "confirmed" | "no_response" | "cancelled" | "rescheduled" | "unsuccessful" | "other";

export default function ActionsPage() {
  const { activeMembership } = useAuth();
  const queryClient = useQueryClient();
  const canExecute = activeMembership ? ["owner", "admin", "manager"].includes(activeMembership.role) : false;
  const [channel, setChannel] = useState<Record<string, Channel>>({});
  const [result, setResult] = useState<Record<string, ContactResult>>({});
  const [note, setNote] = useState<Record<string, string>>({});

  const predictions = useQuery({
    queryKey: ["no-show-predictions", activeMembership?.organization_id],
    queryFn: listNoShowPredictions,
    enabled: Boolean(activeMembership),
  });

  const intervention = useMutation({
    mutationFn: ({ predictionId, selectedChannel, selectedResult, selectedNote }: {
      predictionId: string;
      selectedChannel: Channel;
      selectedResult: ContactResult;
      selectedNote?: string;
    }) => recordNoShowIntervention(predictionId, {
      channel: selectedChannel,
      contact_result: selectedResult,
      note: selectedNote,
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["no-show-predictions"] }),
        queryClient.invalidateQueries({ queryKey: ["no-show-measure-summary"] }),
      ]);
    },
  });

  const accepted = useMemo(
    () => (predictions.data ?? [])
      .filter((item) => item.decision?.decision === "accepted")
      .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()),
    [predictions.data],
  );
  const pending = accepted.filter((item) => !item.intervention);
  const completed = accepted.filter((item) => item.intervention);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">PulseOps Act · M7</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Fila de ações</h1>
        <p className="mt-3 text-[var(--muted)]">
          Recomendações aceitas pelo gestor viram tarefas operacionais. Registre o canal usado e o resultado real do contato.
        </p>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <Metric label="Ações aceitas" value={String(accepted.length)} />
        <Metric label="Pendentes de intervenção" value={String(pending.length)} />
        <Metric label="Intervenções registradas" value={String(completed.length)} />
      </section>

      {intervention.isError && (
        <div className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-800">{intervention.error.message}</div>
      )}

      <section className="mt-6 space-y-4">
        {accepted.length === 0 && (
          <div className="rounded-2xl border border-dashed border-[var(--border)] bg-white p-10 text-center text-[var(--muted)]">
            Nenhuma recomendação aceita aguardando operação. Confirme uma ação na tela Predições.
          </div>
        )}
        {accepted.map((item) => (
          <ActionCard
            key={item.id}
            item={item}
            canExecute={canExecute}
            channel={channel[item.id] ?? "whatsapp"}
            result={result[item.id] ?? "confirmed"}
            note={note[item.id] ?? ""}
            saving={intervention.isPending && intervention.variables?.predictionId === item.id}
            onChannel={(value) => setChannel((current) => ({ ...current, [item.id]: value }))}
            onResult={(value) => setResult((current) => ({ ...current, [item.id]: value }))}
            onNote={(value) => setNote((current) => ({ ...current, [item.id]: value }))}
            onSave={() => intervention.mutate({
              predictionId: item.id,
              selectedChannel: channel[item.id] ?? "whatsapp",
              selectedResult: result[item.id] ?? "confirmed",
              selectedNote: note[item.id]?.trim() || undefined,
            })}
          />
        ))}
      </section>
    </main>
  );
}

function ActionCard({ item, canExecute, channel, result, note, saving, onChannel, onResult, onNote, onSave }: {
  item: NoShowPrediction;
  canExecute: boolean;
  channel: Channel;
  result: ContactResult;
  note: string;
  saving: boolean;
  onChannel: (value: Channel) => void;
  onResult: (value: ContactResult) => void;
  onNote: (value: string) => void;
  onSave: () => void;
}) {
  return (
    <article className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
            {item.equipment_id} · {new Date(item.scheduled_at).toLocaleString("pt-BR")}
          </div>
          <h2 className="mt-2 text-xl font-semibold">Agendamento {item.appointment_id}</h2>
          <div className="mt-2 flex flex-wrap gap-2 text-sm">
            <span className="rounded-full bg-red-50 px-3 py-1 font-semibold text-red-700">Risco {percent.format(item.probability)}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1">Perda esperada {money.format(item.expected_loss)}</span>
          </div>
          <p className="mt-3 text-sm"><strong>Ação:</strong> {item.recommended_action_label}</p>
        </div>
        {item.intervention && (
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">Intervenção registrada ✓</span>
        )}
      </div>

      {item.intervention ? (
        <div className="mt-4 grid gap-3 rounded-xl bg-emerald-50/60 p-4 text-sm md:grid-cols-3">
          <div><span className="block text-xs uppercase text-[var(--muted)]">Canal</span><strong>{channelLabels[item.intervention.channel] ?? item.intervention.channel}</strong></div>
          <div><span className="block text-xs uppercase text-[var(--muted)]">Resultado do contato</span><strong>{resultLabels[item.intervention.contact_result] ?? item.intervention.contact_result}</strong></div>
          <div><span className="block text-xs uppercase text-[var(--muted)]">Executada em</span><strong>{new Date(item.intervention.executed_at).toLocaleString("pt-BR")}</strong></div>
          {item.intervention.note && <p className="md:col-span-3 text-[var(--muted)]">{item.intervention.note}</p>}
        </div>
      ) : (
        <div className="mt-4 grid gap-3 rounded-xl border border-blue-200 bg-blue-50/50 p-4 md:grid-cols-2">
          <label className="text-sm"><span className="font-medium">Canal</span>
            <select value={channel} onChange={(e) => onChannel(e.target.value as Channel)} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2">
              {Object.entries(channelLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="text-sm"><span className="font-medium">Resultado do contato</span>
            <select value={result} onChange={(e) => onResult(e.target.value as ContactResult)} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2">
              {Object.entries(resultLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="text-sm md:col-span-2"><span className="font-medium">Observação opcional</span>
            <textarea value={note} onChange={(e) => onNote(e.target.value)} rows={2} maxLength={2000} className="mt-1 w-full rounded-lg border border-[var(--border)] bg-white p-2" placeholder="Ex.: paciente confirmou presença pelo WhatsApp." />
          </label>
          <div className="md:col-span-2 flex justify-end">
            {canExecute && <button className="button-primary rounded-lg px-4 py-2 text-sm font-semibold" disabled={saving} onClick={onSave}>{saving ? "Registrando…" : "Concluir intervenção"}</button>}
          </div>
        </div>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl border border-[var(--border)] bg-white p-5"><div className="text-sm text-[var(--muted)]">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}

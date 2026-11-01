"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { useAuth } from "@/app/auth-provider";
import { analyzeDataset, uploadCsvBundle } from "@/lib/api";
import type { DatasetBundle } from "@/lib/schemas";

const requiredFiles = ["equipment", "availability", "appointments", "executions"] as const;
type RequiredFile = (typeof requiredFiles)[number];

export default function UploadPage() {
  const router = useRouter();
  const { activeMembership } = useAuth();
  const canImport = activeMembership ? ["owner", "admin", "manager", "analyst"].includes(activeMembership.role) : false;
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<Partial<Record<RequiredFile, File>>>({});
  const [quality, setQuality] = useState<DatasetBundle["quality"] | null>(null);
  const mutation = useMutation({
    mutationFn: async () => {
      for (const key of requiredFiles) if (!files[key]) throw new Error(`Selecione ${key}.csv`);
      const bundle = await uploadCsvBundle(files as Record<RequiredFile, File>);
      setQuality(bundle.quality);
      await analyzeDataset(bundle.dataset.id);
      return bundle;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      router.push("/");
    },
  });

  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate(); }

  if (!canImport) {
    return <main className="mx-auto max-w-4xl px-6 py-10"><div className="rounded-2xl border border-[var(--border)] bg-white p-8">Seu perfil não possui permissão para importar dados.</div></main>;
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">PulseOps Connect</p>
      <h1 className="mt-2 text-4xl font-semibold tracking-tight">Importar operação</h1>
      <p className="mt-3 max-w-2xl text-[var(--muted)]">Envie o bundle operacional. O Connect valida qualidade, normaliza o modelo e aciona o OIE.</p>
      <form onSubmit={submit} className="mt-8 rounded-3xl border border-[var(--border)] bg-white p-7 shadow-sm">
        <div className="grid gap-5 sm:grid-cols-2">{requiredFiles.map((name) => <label key={name} className="rounded-2xl border border-dashed border-[var(--border)] p-5"><span className="block font-medium">{name}.csv</span><span className="mt-1 block text-sm text-[var(--muted)]">Obrigatório</span><input className="mt-4 block w-full text-sm" type="file" accept=".csv,text/csv" onChange={(event) => setFiles((current) => ({ ...current, [name]: event.target.files?.[0] }))} /></label>)}</div>
        <button disabled={mutation.isPending} type="submit" className="button-primary mt-6 rounded-xl px-5 py-3 font-semibold">{mutation.isPending ? "Validando e analisando…" : "Importar e analisar"}</button>
        {mutation.isError && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-800">{mutation.error.message}</p>}
        {quality && <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm"><strong>Qualidade:</strong> {quality.status} · {quality.rows_valid}/{quality.rows_received} linhas válidas · {quality.rows_rejected} rejeitadas</div>}
      </form>
    </main>
  );
}

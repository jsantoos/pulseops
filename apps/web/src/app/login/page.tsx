"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { bootstrapAccount, getBootstrapStatus, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const bootstrapQuery = useQuery({ queryKey: ["auth", "bootstrap-status"], queryFn: getBootstrapStatus, retry: false });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      if (bootstrapQuery.data) {
        return bootstrapAccount({
          email,
          password,
          full_name: fullName,
          organization_name: organizationName || undefined,
        });
      }
      return login({ email, password });
    },
    onSuccess: async (session) => {
      const first = session.user.memberships[0];
      if (first) window.localStorage.setItem("pulseops.active_organization", first.organization_id);
      await queryClient.invalidateQueries({ queryKey: ["auth"] });
      router.replace("/");
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-6 py-12">
      <div className="w-full max-w-md rounded-3xl border border-[var(--border)] bg-white p-8 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--accent)] font-semibold text-white">P</span>
          <div>
            <div className="font-semibold">PulseOps</div>
            <div className="text-xs text-[var(--muted)]">Operational Decision Intelligence</div>
          </div>
        </div>

        <h1 className="mt-8 text-3xl font-semibold tracking-tight">
          {bootstrapQuery.data ? "Configurar primeiro acesso" : "Entrar"}
        </h1>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          {bootstrapQuery.data
            ? "Crie o primeiro usuário proprietário. Se já existir uma única organização no banco, ela será reaproveitada automaticamente."
            : "Acesse as oportunidades da organização à qual você pertence."}
        </p>

        <form onSubmit={submit} className="mt-7 space-y-4">
          {bootstrapQuery.data && (
            <>
              <Field label="Nome completo" value={fullName} onChange={setFullName} autoComplete="name" />
              <Field label="Organização (somente banco novo)" value={organizationName} onChange={setOrganizationName} autoComplete="organization" required={false} />
            </>
          )}
          <Field label="E-mail" type="email" value={email} onChange={setEmail} autoComplete="email" />
          <Field label="Senha" type="password" value={password} onChange={setPassword} autoComplete={bootstrapQuery.data ? "new-password" : "current-password"} minLength={bootstrapQuery.data ? 12 : 8} />
          {bootstrapQuery.data && <p className="text-xs text-[var(--muted)]">Use ao menos 12 caracteres no primeiro acesso.</p>}
          <button
            disabled={mutation.isPending || bootstrapQuery.isPending}
            className="button-primary w-full rounded-xl px-5 py-3 font-semibold"
          >
            {mutation.isPending ? "Processando…" : bootstrapQuery.data ? "Criar acesso" : "Entrar"}
          </button>
          {mutation.isError && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{mutation.error.message}</p>}
          {bootstrapQuery.isError && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-800">Não foi possível verificar o estado de autenticação.</p>}
        </form>
      </div>
    </main>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
  required = true,
  minLength,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  autoComplete: string;
  required?: boolean;
  minLength?: number;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        required={required}
        minLength={minLength}
        className="mt-2 w-full rounded-xl border border-[var(--border)] px-3 py-3 outline-none focus:border-[var(--accent)]"
      />
    </label>
  );
}

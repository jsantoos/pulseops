"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/app/auth-provider";

const roleLabels: Record<string, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  manager: "Gestor",
  analyst: "Analista",
  viewer: "Visualizador",
};

export function AppHeader() {
  const pathname = usePathname();
  const { session, activeMembership, setActiveOrganization, signOut } = useAuth();
  const canImport = activeMembership ? ["owner", "admin", "manager", "analyst"].includes(activeMembership.role) : false;

  if (pathname === "/login") return null;

  return (
    <header className="border-b border-[var(--border)] bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-5 px-6 py-4">
        <Link href="/" className="flex items-center gap-3 font-semibold tracking-tight">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--accent)] text-white">P</span>
          <span>PulseOps</span>
        </Link>
        <div className="flex items-center gap-4">
          {session && session.user.memberships.length > 0 && (
            <select
              aria-label="Organização ativa"
              value={activeMembership?.organization_id ?? ""}
              onChange={(event) => setActiveOrganization(event.target.value)}
              className="rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm"
            >
              {session.user.memberships.map((membership) => (
                <option key={membership.organization_id} value={membership.organization_id}>
                  {membership.organization_name}
                </option>
              ))}
            </select>
          )}
          <nav className="flex items-center gap-2 text-sm">
            <Link href="/executive" className="rounded-lg px-3 py-2 hover:bg-slate-100">Visão executiva</Link>
            <Link href="/" className="rounded-lg px-3 py-2 hover:bg-slate-100">Oportunidades</Link>
            <Link href="/opportunities/analytics" className="rounded-lg px-3 py-2 hover:bg-slate-100">Analytics OIE</Link>
            <Link href="/opportunities/evolution" className="rounded-lg px-3 py-2 hover:bg-slate-100">Evolução</Link>
            <Link href="/predict" className="rounded-lg px-3 py-2 hover:bg-slate-100">Predições</Link>
            <Link href="/actions" className="rounded-lg px-3 py-2 hover:bg-slate-100">Fila de ações</Link>
            <Link href="/measure" className="rounded-lg px-3 py-2 hover:bg-slate-100">Resultados</Link>
            {canImport && <Link href="/upload" className="rounded-lg px-3 py-2 hover:bg-slate-100">Importar dados</Link>}
          </nav>
          {session && (
            <div className="hidden text-right text-xs text-[var(--muted)] lg:block">
              <div className="font-medium text-[var(--foreground)]">{session.user.full_name}</div>
              <div>{activeMembership ? roleLabels[activeMembership.role] ?? activeMembership.role : "Sem organização"}</div>
            </div>
          )}
          {session && (
            <button
              onClick={() => void signOut()}
              className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm hover:bg-slate-50"
            >
              Sair
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

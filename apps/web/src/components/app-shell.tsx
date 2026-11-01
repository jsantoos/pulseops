"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/app/auth-provider";

const roleLabels: Record<string, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  manager: "Gestor",
  analyst: "Analista",
  viewer: "Visualizador",
};

type NavItem = {
  href: string;
  label: string;
  icon: IconName;
  exact?: boolean;
  requiresImport?: boolean;
};

type IconName =
  | "executive"
  | "opportunities"
  | "analytics"
  | "evolution"
  | "predict"
  | "actions"
  | "results"
  | "upload"
  | "user"
  | "logout"
  | "menu"
  | "chevron";

const navigation: Array<{ label: string; items: NavItem[] }> = [
  {
    label: "Operação",
    items: [
      { href: "/executive", label: "Visão executiva", icon: "executive", exact: true },
      { href: "/", label: "Oportunidades", icon: "opportunities", exact: true },
      { href: "/opportunities/analytics", label: "Analytics OIE", icon: "analytics", exact: true },
      { href: "/opportunities/evolution", label: "Evolução", icon: "evolution", exact: true },
      { href: "/measure", label: "Resultados", icon: "results", exact: true },
    ],
  },
  {
    label: "IA & previsões",
    items: [
      { href: "/predict", label: "Predições (No-show)", icon: "predict", exact: true },
      { href: "/actions", label: "Fila de ações", icon: "actions", exact: true },
    ],
  },
  {
    label: "Dados",
    items: [
      { href: "/upload", label: "Importar dados", icon: "upload", exact: true, requiresImport: true },
    ],
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session, activeMembership, setActiveOrganization, signOut } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  if (pathname === "/login") return <>{children}</>;

  const canImport = activeMembership
    ? ["owner", "admin", "manager", "analyst"].includes(activeMembership.role)
    : false;

  const closeMobile = () => setMobileOpen(false);

  const sidebar = (
    <div className="flex h-full flex-col bg-white">
      <div className={`flex h-20 items-center border-b border-[var(--border)] px-4 ${collapsed ? "justify-center" : "justify-between"}`}>
        <Link href="/executive" onClick={closeMobile} className="flex min-w-0 items-center gap-3 font-semibold tracking-tight">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)] text-white">P</span>
          {!collapsed && <span className="truncate text-lg">PulseOps</span>}
        </Link>
        {!collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(true)}
            className="hidden h-9 w-9 place-items-center rounded-lg border border-[var(--border)] text-[var(--muted)] hover:bg-slate-50 lg:grid"
            aria-label="Recolher menu"
            title="Recolher menu"
          >
            <Icon name="chevron" className="h-4 w-4 rotate-180" />
          </button>
        )}
      </div>

      <div className="border-b border-[var(--border)] px-3 py-4">
        {session && session.user.memberships.length > 0 && (
          collapsed ? (
            <div className="grid place-items-center" title={activeMembership?.organization_name ?? "Organização"}>
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-slate-100 text-xs font-semibold text-[var(--accent)]">
                {(activeMembership?.organization_name ?? "O").slice(0, 2).toUpperCase()}
              </span>
            </div>
          ) : (
            <select
              aria-label="Organização ativa"
              value={activeMembership?.organization_id ?? ""}
              onChange={(event) => setActiveOrganization(event.target.value)}
              className="w-full rounded-xl border border-[var(--border)] bg-white px-3 py-2.5 text-sm outline-none focus:border-[var(--accent)]"
            >
              {session.user.memberships.map((membership) => (
                <option key={membership.organization_id} value={membership.organization_id}>
                  {membership.organization_name}
                </option>
              ))}
            </select>
          )
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {navigation.map((group) => {
          const visibleItems = group.items.filter((item) => !item.requiresImport || canImport);
          if (!visibleItems.length) return null;
          return (
            <div key={group.label} className="mb-5 last:mb-0">
              {!collapsed && (
                <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
                  {group.label}
                </div>
              )}
              <div className="space-y-1">
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.href}
                    item={item}
                    pathname={pathname}
                    collapsed={collapsed}
                    onNavigate={closeMobile}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] p-3">
        {session && (
          <div className={`mb-2 rounded-xl bg-slate-50 ${collapsed ? "p-2" : "p-3"}`}>
            <div className={`flex items-center ${collapsed ? "justify-center" : "gap-3"}`} title={session.user.full_name}>
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--accent-soft)] text-xs font-semibold text-[var(--accent)]">
                {initials(session.user.full_name)}
              </span>
              {!collapsed && (
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{session.user.full_name}</div>
                  <div className="truncate text-xs text-[var(--muted)]">
                    {activeMembership ? roleLabels[activeMembership.role] ?? activeMembership.role : "Sem organização"}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {session && (
          <button
            type="button"
            onClick={() => void signOut()}
            className={`flex w-full items-center rounded-xl px-3 py-2.5 text-sm hover:bg-slate-50 ${collapsed ? "justify-center" : "gap-3"}`}
            title="Sair"
          >
            <Icon name="logout" className="h-5 w-5 shrink-0" />
            {!collapsed && <span>Sair</span>}
          </button>
        )}

        {collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            className="mt-2 hidden w-full place-items-center rounded-xl border border-[var(--border)] py-2.5 text-[var(--muted)] hover:bg-slate-50 lg:grid"
            aria-label="Expandir menu"
            title="Expandir menu"
          >
            <Icon name="chevron" className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen lg:flex">
      <aside className={`hidden shrink-0 border-r border-[var(--border)] transition-[width] duration-200 lg:sticky lg:top-0 lg:block lg:h-screen ${collapsed ? "lg:w-20" : "lg:w-64"}`}>
        {sidebar}
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Fechar menu"
            className="absolute inset-0 bg-slate-950/30"
            onClick={closeMobile}
          />
          <aside className="relative h-full w-[min(19rem,88vw)] border-r border-[var(--border)] shadow-xl">
            {sidebar}
          </aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--border)] bg-white/95 px-4 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)]"
            aria-label="Abrir menu"
          >
            <Icon name="menu" className="h-5 w-5" />
          </button>
          <Link href="/executive" className="flex items-center gap-2 font-semibold">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--accent)] text-sm text-white">P</span>
            PulseOps
          </Link>
          <div className="w-10" />
        </header>
        {children}
      </div>
    </div>
  );
}

function NavLink({
  item,
  pathname,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  pathname: string;
  collapsed: boolean;
  onNavigate: () => void;
}) {
  const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
      aria-current={active ? "page" : undefined}
      className={`flex items-center rounded-xl px-3 py-2.5 text-sm transition-colors ${
        collapsed ? "justify-center" : "gap-3"
      } ${
        active
          ? "bg-[var(--accent-soft)] font-semibold text-[var(--accent)]"
          : "text-slate-700 hover:bg-slate-50"
      }`}
    >
      <Icon name={item.icon} className="h-5 w-5 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </Link>
  );
}

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function Icon({ name, className }: { name: IconName; className?: string }) {
  const common = {
    className,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
    "aria-hidden": true,
  } as const;

  const paths: Record<IconName, React.ReactNode> = {
    executive: <><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M7 15v2M11 11v6M15 8v9M19 13v4" /></>,
    opportunities: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /><path d="m16.5 7.5 3-3M17 4.5h2.5V7" /></>,
    analytics: <><path d="M4 19V9M9 19V5M14 19v-7M19 19V3" /><path d="M2 19h20" /></>,
    evolution: <><path d="m3 17 6-6 4 4 7-8" /><path d="M15 7h5v5" /></>,
    predict: <><path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-2 2.8V13a3 3 0 0 0 2 2.8V17a3 3 0 0 0 3 3" /><path d="M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 2 2.8V13a3 3 0 0 1-2 2.8V17a3 3 0 0 1-3 3M12 3v18M8 9h4M12 15h4" /></>,
    actions: <><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M8 12l2 2 4-4M8 17h8" /></>,
    results: <><path d="M5 20V10M12 20V4M19 20v-7" /><path d="M3 20h18" /></>,
    upload: <><path d="M12 16V4M8 8l4-4 4 4" /><path d="M5 14v5h14v-5" /></>,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
    logout: <><path d="M10 5H5v14h5M14 8l4 4-4 4M18 12H9" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
    chevron: <path d="m9 6 6 6-6 6" />,
  };

  return <svg {...common}>{paths[name]}</svg>;
}

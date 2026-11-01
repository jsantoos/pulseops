"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  clearActiveOrganizationId,
  getActiveOrganizationId,
  getMe,
  logout,
  setActiveOrganizationId,
} from "@/lib/api";
import type { AuthSession, Membership } from "@/lib/schemas";

type AuthContextValue = {
  session: AuthSession | null;
  activeMembership: Membership | null;
  setActiveOrganization: (organizationId: string) => void;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [activeOrganizationId, setActiveOrganizationIdState] = useState<string | null>(() => getActiveOrganizationId());
  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
    retry: false,
    enabled: pathname !== "/login",
  });

  useEffect(() => {
    if (!meQuery.data) return;
    const memberships = meQuery.data.user.memberships;
    const selected =
      memberships.find((item) => item.organization_id === activeOrganizationId) ??
      memberships[0] ??
      null;
    if (selected) setActiveOrganizationId(selected.organization_id);
  }, [activeOrganizationId, meQuery.data]);

  useEffect(() => {
    if (pathname === "/login") return;
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      router.replace("/login");
    }
  }, [meQuery.error, pathname, router]);

  const value = useMemo<AuthContextValue>(() => {
    const memberships = meQuery.data?.user.memberships ?? [];
    const activeMembership = memberships.find(
      (item) => item.organization_id === activeOrganizationId,
    ) ?? memberships[0] ?? null;

    return {
      session: meQuery.data ?? null,
      activeMembership,
      setActiveOrganization: (organizationId: string) => {
        setActiveOrganizationId(organizationId);
        setActiveOrganizationIdState(organizationId);
        void queryClient.invalidateQueries();
      },
      signOut: async () => {
        try {
          await logout();
        } finally {
          clearActiveOrganizationId();
          setActiveOrganizationIdState(null);
          queryClient.clear();
          router.replace("/login");
        }
      },
    };
  }, [activeOrganizationId, meQuery.data, queryClient, router]);

  if (pathname !== "/login" && meQuery.isPending) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-2xl border border-[var(--border)] bg-white p-8">Validando sessão…</div>
      </main>
    );
  }

  if (pathname !== "/login" && meQuery.isError) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-2xl border border-[var(--border)] bg-white p-8">Redirecionando para o acesso…</div>
      </main>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

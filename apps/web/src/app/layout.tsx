import type { Metadata } from "next";

import "./globals.css";
import { AppShell } from "@/components/app-shell";
import { AuthProvider } from "./auth-provider";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "PulseOps",
  description: "Operational intelligence for diagnostic centers",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <Providers>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </Providers>
      </body>
    </html>
  );
}

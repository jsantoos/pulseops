import { OpportunityInbox } from "@/components/opportunity-inbox";

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-8 max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">Inteligência operacional</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Caixa de oportunidades</h1>
        <p className="mt-3 text-[var(--muted)]">Priorize decisões com base em impacto econômico, evidências disponíveis e urgência operacional.</p>
      </div>
      <OpportunityInbox />
    </main>
  );
}

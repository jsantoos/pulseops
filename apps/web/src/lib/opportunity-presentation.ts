import type { Opportunity } from "./schemas";
import { currency, durationMinutes, numberPtBr, percentage } from "./format";

export type EvidenceKind = "observed" | "derived" | "estimate";

export type PresentedEvidence = {
  key: string;
  label: string;
  value: string;
  kind: EvidenceKind;
};

const categoryLabels: Record<string, string> = {
  capacity: "Capacidade",
  cancellation: "Cancelamentos e ausências",
};

const severityLabels: Record<string, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
};

const statusLabels: Record<string, string> = {
  open: "Aberta",
  accepted: "Aceita",
  dismissed: "Descartada",
  executed: "Executada",
  measured: "Resultado mensurado",
};

const actionTranslations: Record<string, string> = {
  "Review idle windows and compatible exam durations":
    "Revisar janelas ociosas e identificar exames com duração compatível.",
  "Prioritize eligible patients for recovered capacity":
    "Priorizar pacientes elegíveis para ocupar a capacidade recuperável.",
  "Review cancellation/no-show patterns by exam type and lead time":
    "Analisar padrões de cancelamento e ausência por tipo de exame e antecedência.",
  "Test targeted confirmations or wait-list recovery for high-value slots":
    "Testar confirmações direcionadas ou lista de espera para recuperar horários de maior valor.",
};

const titleTranslations: Record<string, string> = {
  "RM-02 below target utilization": "RM-02 com utilização abaixo da meta",
  "RM-02 cancellation/no-show loss": "Perda por cancelamentos e ausências na RM-02",
};

export function categoryLabel(value: string): string {
  return categoryLabels[value] ?? value;
}

export function severityLabel(value: string): string {
  return severityLabels[value] ?? value;
}

export function statusLabel(value: string): string {
  return statusLabels[value] ?? value;
}

export function opportunityTitle(opportunity: Opportunity): string {
  return titleTranslations[opportunity.title] ?? opportunity.title;
}

export function actionLabel(action: string): string {
  return actionTranslations[action] ?? action;
}

export function priorityLevel(score: number): { label: string; description: string } {
  if (score >= 75) return { label: "Crítica", description: "Exige avaliação imediata." };
  if (score >= 50) return { label: "Alta", description: "Deve ser priorizada entre as oportunidades abertas." };
  if (score >= 25) return { label: "Moderada", description: "Relevante, mas abaixo das prioridades principais." };
  return { label: "Baixa", description: "Pode aguardar enquanto oportunidades mais relevantes são tratadas." };
}

function numericEvidence(opportunity: Opportunity, key: string): number | undefined {
  const value = opportunity.evidence[key];
  return typeof value === "number" ? value : undefined;
}

function stringEvidence(opportunity: Opportunity, key: string): string | undefined {
  const value = opportunity.evidence[key];
  return typeof value === "string" ? value : undefined;
}

export function presentedEvidence(opportunity: Opportunity): PresentedEvidence[] {
  if (opportunity.category === "capacity") {
    const values: Array<PresentedEvidence | undefined> = [
      stringEvidence(opportunity, "equipment_id")
        ? { key: "equipment_id", label: "Equipamento", value: stringEvidence(opportunity, "equipment_id")!, kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "utilization") !== undefined
        ? { key: "utilization", label: "Utilização atual", value: percentage(numericEvidence(opportunity, "utilization")!), kind: "derived" }
        : undefined,
      numericEvidence(opportunity, "target_utilization") !== undefined
        ? { key: "target_utilization", label: "Meta de utilização", value: percentage(numericEvidence(opportunity, "target_utilization")!), kind: "estimate" }
        : undefined,
      numericEvidence(opportunity, "available_minutes") !== undefined
        ? { key: "available_minutes", label: "Capacidade disponível", value: durationMinutes(numericEvidence(opportunity, "available_minutes")!), kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "realized_minutes") !== undefined
        ? { key: "realized_minutes", label: "Tempo efetivamente realizado", value: durationMinutes(numericEvidence(opportunity, "realized_minutes")!), kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "recoverable_minutes") !== undefined
        ? { key: "recoverable_minutes", label: "Capacidade recuperável até a meta", value: durationMinutes(numericEvidence(opportunity, "recoverable_minutes")!), kind: "derived" }
        : undefined,
      numericEvidence(opportunity, "revenue_per_realized_minute") !== undefined
        ? { key: "revenue_per_realized_minute", label: "Receita média por minuto realizado", value: `${currency(numericEvidence(opportunity, "revenue_per_realized_minute")!)} / min`, kind: "estimate" }
        : undefined,
    ];
    return values.filter((value): value is PresentedEvidence => Boolean(value));
  }

  if (opportunity.category === "cancellation") {
    const values: Array<PresentedEvidence | undefined> = [
      stringEvidence(opportunity, "equipment_id")
        ? { key: "equipment_id", label: "Equipamento", value: stringEvidence(opportunity, "equipment_id")!, kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "total_appointments") !== undefined
        ? { key: "total_appointments", label: "Agendamentos analisados", value: numberPtBr(numericEvidence(opportunity, "total_appointments")!), kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "cancelled") !== undefined
        ? { key: "cancelled", label: "Cancelamentos", value: numberPtBr(numericEvidence(opportunity, "cancelled")!), kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "no_shows") !== undefined
        ? { key: "no_shows", label: "Ausências (no-show)", value: numberPtBr(numericEvidence(opportunity, "no_shows")!), kind: "observed" }
        : undefined,
      numericEvidence(opportunity, "loss_rate") !== undefined
        ? { key: "loss_rate", label: "Taxa de perda de agenda", value: percentage(numericEvidence(opportunity, "loss_rate")!), kind: "derived" }
        : undefined,
      numericEvidence(opportunity, "lost_revenue") !== undefined
        ? { key: "lost_revenue", label: "Receita associada às perdas", value: currency(numericEvidence(opportunity, "lost_revenue")!), kind: "derived" }
        : undefined,
    ];
    return values.filter((value): value is PresentedEvidence => Boolean(value));
  }

  return Object.entries(opportunity.evidence).map(([key, value]) => ({
    key,
    label: key.replaceAll("_", " "),
    value: String(value),
    kind: "observed" as const,
  }));
}

export function explanation(opportunity: Opportunity): {
  headline: string;
  body: string;
  formula?: string;
  caveat: string;
} {
  if (opportunity.category === "capacity") {
    const available = numericEvidence(opportunity, "available_minutes") ?? 0;
    const realized = numericEvidence(opportunity, "realized_minutes") ?? 0;
    const target = numericEvidence(opportunity, "target_utilization") ?? 0;
    const recoverable = numericEvidence(opportunity, "recoverable_minutes") ?? 0;
    const revenuePerMinute = numericEvidence(opportunity, "revenue_per_realized_minute") ?? 0;
    return {
      headline: "Há capacidade operacional não utilizada até a meta configurada.",
      body: `O equipamento teve ${durationMinutes(realized)} realizados em ${durationMinutes(available)} disponíveis. Para atingir a meta de ${percentage(target)}, o OIE identificou ${durationMinutes(recoverable)} de capacidade potencialmente recuperável.`,
      formula: `${durationMinutes(recoverable)} × ${currency(revenuePerMinute)}/min = ${currency(opportunity.estimated_gain)}`,
      caveat: "O valor é uma estimativa de potencial, não receita garantida. A recuperação depende de demanda, elegibilidade de pacientes e restrições operacionais.",
    };
  }

  if (opportunity.category === "cancellation") {
    const total = numericEvidence(opportunity, "total_appointments") ?? 0;
    const cancelled = numericEvidence(opportunity, "cancelled") ?? 0;
    const noShows = numericEvidence(opportunity, "no_shows") ?? 0;
    const lossRate = numericEvidence(opportunity, "loss_rate") ?? 0;
    return {
      headline: "Cancelamentos e ausências estão consumindo capacidade e receita.",
      body: `Em ${numberPtBr(total)} agendamentos analisados, houve ${numberPtBr(cancelled)} cancelamento(s) e ${numberPtBr(noShows)} ausência(s), equivalentes a ${percentage(lossRate)} dos horários analisados.`,
      formula: `Receita associada aos horários perdidos: ${currency(opportunity.estimated_gain)}`,
      caveat: "Este valor representa receita associada às perdas observadas. A parcela efetivamente recuperável será menor ou igual a esse potencial e deverá ser medida após a intervenção.",
    };
  }

  return {
    headline: "O OIE identificou um padrão operacional relevante.",
    body: "A oportunidade foi gerada a partir dos dados e regras do motor operacional.",
    caveat: "Revise as evidências antes de executar qualquer ação.",
  };
}

export function evidenceKindLabel(kind: EvidenceKind): string {
  if (kind === "observed") return "Dado observado";
  if (kind === "derived") return "Cálculo do OIE";
  return "Premissa / estimativa";
}

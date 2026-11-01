import {
  authSchema,
  executiveSummarySchema,
  bootstrapStatusSchema,
  datasetBundleSchema,
  opportunitiesSchema,
  opportunityAnalyticsSchema,
  opportunityHistorySchema,
  opportunityTemporalSchema,
  opportunitySchema,
  noShowPredictionsSchema,
  modelRunsSchema,
  noShowTrainResponseSchema,
  type AuthSession,
  type ExecutiveSummary,
  type DatasetBundle,
  type Opportunity,
  type OpportunityAnalytics,
  type OpportunityHistory,
  type OpportunityTemporal,
  type NoShowPrediction,
  type ModelRun,
  type NoShowTrainResponse,
  noShowDecisionSchema,
  type NoShowDecision,
  noShowInterventionSchema,
  noShowOutcomeSchema,
  noShowMeasureSummarySchema,
  type NoShowIntervention,
  type NoShowOutcome,
  type NoShowMeasureSummary,
} from "./schemas";

const API_URL = process.env.NEXT_PUBLIC_PULSEOPS_API_URL ?? "http://localhost:8000";
const ACTIVE_ORG_KEY = "pulseops.active_organization";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getActiveOrganizationId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACTIVE_ORG_KEY);
}

export function setActiveOrganizationId(value: string): void {
  if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_ORG_KEY, value);
}

export function clearActiveOrganizationId(): void {
  if (typeof window !== "undefined") window.localStorage.removeItem(ACTIVE_ORG_KEY);
}

function formatApiDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return translateApiMessage(detail);
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const candidate = item as { msg?: unknown; loc?: unknown[] };
        if (typeof candidate.msg !== "string") return null;
        const field = Array.isArray(candidate.loc) ? candidate.loc.at(-1) : null;
        return translateValidationMessage(typeof field === "string" ? field : null, candidate.msg);
      })
      .filter((value): value is string => Boolean(value));
    if (messages.length) return messages.join(" ");
  }
  return fallback;
}

function translateValidationMessage(field: string | null, message: string): string {
  if (field === "password" && message.toLowerCase().includes("at least 12")) {
    return "A senha deve conter pelo menos 12 caracteres.";
  }
  if (field === "password" && message.toLowerCase().includes("at least 8")) {
    return "A senha deve conter pelo menos 8 caracteres.";
  }
  return translateApiMessage(message);
}

function translateApiMessage(message: string): string {
  const known: Record<string, string> = {
    "invalid credentials": "E-mail ou senha inválidos.",
    "authentication required": "Sua sessão terminou. Entre novamente.",
    "invalid session": "Sua sessão não é mais válida. Entre novamente.",
    "session expired": "Sua sessão expirou. Entre novamente.",
    "insufficient role": "Seu perfil não possui permissão para executar esta ação.",
    "organization access denied": "Você não possui acesso a esta organização.",
    "user already exists": "Já existe um usuário com este e-mail.",
  };
  return known[message] ?? message;
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const method = (init?.method ?? "GET").toUpperCase();
  const organizationId = getActiveOrganizationId();

  if (organizationId) headers.set("X-PulseOps-Organization", organizationId);
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers.set("X-PulseOps-Request", "web");

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const body = await response.text();
    let message = body || `PulseOps API returned ${response.status}`;
    try {
      const parsed = JSON.parse(body) as { detail?: unknown };
      message = formatApiDetail(parsed.detail, message);
    } catch {
      // Keep the plain response body.
    }
    throw new ApiError(message, response.status);
  }
  return response;
}

export async function getBootstrapStatus(): Promise<boolean> {
  const response = await request("/v1/auth/bootstrap-status");
  return bootstrapStatusSchema.parse(await response.json()).bootstrap_required;
}

export async function bootstrapAccount(payload: {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
}): Promise<AuthSession> {
  const response = await request("/v1/auth/bootstrap", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return authSchema.parse(await response.json());
}

export async function login(payload: { email: string; password: string }): Promise<AuthSession> {
  const response = await request("/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return authSchema.parse(await response.json());
}

export async function logout(): Promise<void> {
  await request("/v1/auth/logout", { method: "POST" });
}

export async function getMe(): Promise<AuthSession> {
  const response = await request("/v1/auth/me");
  return authSchema.parse(await response.json());
}

export async function listOpportunities(status = "open"): Promise<Opportunity[]> {
  const response = await request(`/v1/opportunities?status=${encodeURIComponent(status)}`);
  return opportunitiesSchema.parse(await response.json());
}

export async function getExecutiveSummary(): Promise<ExecutiveSummary> {
  const response = await request("/v1/executive/summary");
  return executiveSummarySchema.parse(await response.json());
}

export async function getOpportunityHistory(opportunityId: string): Promise<OpportunityHistory> {
  const response = await request(`/v1/opportunities/${encodeURIComponent(opportunityId)}/history`);
  return opportunityHistorySchema.parse(await response.json());
}

export async function getOpportunityAnalytics(): Promise<OpportunityAnalytics> {
  const response = await request("/v1/opportunities/analytics");
  return opportunityAnalyticsSchema.parse(await response.json());
}

export async function getOpportunityTemporal(): Promise<OpportunityTemporal> {
  const response = await request("/v1/opportunities/temporal");
  return opportunityTemporalSchema.parse(await response.json());
}

export async function uploadCsvBundle(
  files: Record<"equipment" | "availability" | "appointments" | "executions", File>,
): Promise<DatasetBundle> {
  const formData = new FormData();
  for (const [name, file] of Object.entries(files)) formData.append(name, file);
  const response = await request("/v1/datasets/csv-bundle", {
    method: "POST",
    body: formData,
  });
  return datasetBundleSchema.parse(await response.json());
}

export async function analyzeDataset(datasetId: string): Promise<void> {
  await request(`/v1/datasets/${encodeURIComponent(datasetId)}/analyze`, { method: "POST" });
}

export async function getOpportunity(opportunityId: string): Promise<Opportunity> {
  const response = await request(`/v1/opportunities/${encodeURIComponent(opportunityId)}`);
  return opportunitySchema.parse(await response.json());
}

export async function decideOpportunity(
  opportunityId: string,
  payload: { decision: "accepted" | "dismissed"; notes?: string },
): Promise<Opportunity> {
  const response = await request(`/v1/opportunities/${encodeURIComponent(opportunityId)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return opportunitySchema.parse(await response.json());
}

export async function recordOpportunityOutcome(
  opportunityId: string,
  payload: { measured_gain?: number; notes?: string },
): Promise<void> {
  await request(`/v1/opportunities/${encodeURIComponent(opportunityId)}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}


export async function trainLatestNoShowModel(): Promise<NoShowTrainResponse> {
  const response = await request("/v1/ml/no-show/train-latest", { method: "POST" });
  return noShowTrainResponseSchema.parse(await response.json());
}

export async function listNoShowPredictions(): Promise<NoShowPrediction[]> {
  const response = await request("/v1/ml/no-show/predictions");
  return noShowPredictionsSchema.parse(await response.json());
}

export async function listModelRuns(): Promise<ModelRun[]> {
  const response = await request("/v1/ml/model-runs");
  return modelRunsSchema.parse(await response.json());
}


export async function decideNoShowPrediction(
  predictionId: string,
  payload: { decision: "accepted" | "dismissed"; note?: string },
): Promise<NoShowDecision> {
  const response = await request(`/v1/ml/no-show/predictions/${encodeURIComponent(predictionId)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return noShowDecisionSchema.parse(await response.json());
}


export async function recordNoShowIntervention(
  predictionId: string,
  payload: {
    channel: "whatsapp" | "phone" | "sms" | "email" | "other";
    contact_result: "confirmed" | "no_response" | "cancelled" | "rescheduled" | "unsuccessful" | "other";
    note?: string;
  },
): Promise<NoShowIntervention> {
  const response = await request(`/v1/ml/no-show/predictions/${encodeURIComponent(predictionId)}/intervention`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return noShowInterventionSchema.parse(await response.json());
}


export async function recordNoShowOutcome(
  predictionId: string,
  payload: {
    intervention_executed: boolean;
    observed_status?: "attended" | "no_show" | "cancelled";
    realized_revenue?: number;
    measured_recovered_value?: number;
    note?: string;
  },
): Promise<NoShowOutcome> {
  const response = await request(`/v1/ml/no-show/predictions/${encodeURIComponent(predictionId)}/outcome`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return noShowOutcomeSchema.parse(await response.json());
}

export async function getNoShowMeasureSummary(): Promise<NoShowMeasureSummary> {
  const response = await request("/v1/ml/no-show/measure-summary");
  return noShowMeasureSummarySchema.parse(await response.json());
}

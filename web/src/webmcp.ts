import { apiRequest } from "./lib/api";
import type { ChangeReviewDraft, RunDetail, ScenarioSummary } from "./types";

export const WEBMCP_REVIEW_CREATED = "cutoverproof:webmcp-review-created";
export const WEBMCP_OPEN_REPAIR = "cutoverproof:webmcp-open-repair";

type JsonSchema = Record<string, unknown>;
type ToolAnnotations = { readOnlyHint?: boolean; untrustedContentHint?: boolean };
type ToolDefinition = {
  name: string;
  title: string;
  description: string;
  inputSchema: JsonSchema;
  annotations?: ToolAnnotations;
  execute: (input: unknown, options?: { signal?: AbortSignal }) => Promise<unknown>;
};
type ModelContext = {
  registerTool: (tool: ToolDefinition, options?: { signal?: AbortSignal }) => Promise<void>;
};

declare global {
  interface Document {
    modelContext?: ModelContext;
  }
}

export interface WebMcpRegistration {
  supported: boolean;
  toolNames: string[];
  ready: Promise<void>;
  unregister: () => void;
}

function objectInput(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Tool input must be an object.");
  }
  return value as Record<string, unknown>;
}

function requiredString(input: Record<string, unknown>, name: string, maxLength: number): string {
  const value = input[name];
  if (typeof value !== "string" || !value.trim() || value.length > maxLength) {
    throw new Error(`${name} must be a non-empty string of at most ${maxLength} characters.`);
  }
  return value.trim();
}

function emptySchema(): JsonSchema {
  return { type: "object", properties: {}, additionalProperties: false };
}

const tools: ToolDefinition[] = [
  {
    name: "list_migration_contracts",
    title: "List migration contracts",
    description: "List the bounded PostgreSQL migration contracts available in the signed-in CutoverProof workspace. Returns summaries only and does not execute a migration.",
    inputSchema: emptySchema(),
    annotations: { readOnlyHint: true, untrustedContentHint: true },
    execute: async () => {
      const contracts = await apiRequest<ScenarioSummary[]>("/api/webmcp/contracts");
      return {
        contracts,
        next_step: "Inspect one contract before preparing a review.",
        safety_boundary: "No database operation was executed.",
      };
    },
  },
  {
    name: "inspect_migration_contract",
    title: "Inspect a migration contract",
    description: "Read phases, declared operations, invariants, allowed repairs, and authority boundaries for one CutoverProof migration contract. Raw SQL and hidden evaluator answers are never returned.",
    inputSchema: {
      type: "object",
      properties: {
        scenario_id: { type: "string", pattern: "^[a-z0-9][a-z0-9_-]{0,79}$", description: "Contract identifier returned by list_migration_contracts." },
      },
      required: ["scenario_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: true, untrustedContentHint: true },
    execute: async (raw) => {
      const scenarioId = requiredString(objectInput(raw), "scenario_id", 80);
      return apiRequest(`/api/webmcp/contracts/${encodeURIComponent(scenarioId)}`);
    },
  },
  {
    name: "create_change_review_draft",
    title: "Prepare a human change review",
    description: "Create an idempotent, visible review draft for a declared migration contract. This does not start PostgreSQL, run SQL, approve a repair, or deploy anything; a human must review and explicitly start the sandbox assessment.",
    inputSchema: {
      type: "object",
      properties: {
        scenario_id: { type: "string", pattern: "^[a-z0-9][a-z0-9_-]{0,79}$" },
        objective: { type: "string", minLength: 12, maxLength: 600, description: "The outcome the engineer wants from this change review." },
        risk_focus: {
          type: "array",
          maxItems: 5,
          uniqueItems: true,
          items: { type: "string", enum: ["compatibility_window", "stale_writes", "cutover_ordering", "rollback_readiness", "data_invariants"] },
        },
        idempotency_key: { type: "string", pattern: "^[A-Za-z0-9][A-Za-z0-9_.:-]{7,119}$", description: "Stable unique key so retries do not create duplicate drafts." },
      },
      required: ["scenario_id", "objective", "idempotency_key"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    execute: async (raw) => {
      const input = objectInput(raw);
      const riskFocus = Array.isArray(input.risk_focus)
        ? input.risk_focus.filter((item): item is string => typeof item === "string")
        : [];
      const draft = await apiRequest<ChangeReviewDraft>("/api/webmcp/review-drafts", {
        method: "POST",
        body: JSON.stringify({
          scenario_id: requiredString(input, "scenario_id", 80),
          objective: requiredString(input, "objective", 600),
          risk_focus: riskFocus,
          idempotency_key: requiredString(input, "idempotency_key", 120),
        }),
      });
      window.dispatchEvent(new CustomEvent(WEBMCP_REVIEW_CREATED, { detail: draft }));
      return {
        draft,
        execution_started: false,
        requires_human_action: true,
        next_step: "Ask the engineer to review the visible draft and start the sandbox assessment.",
      };
    },
  },
  {
    name: "read_verified_migration_evidence",
    title: "Read verified migration evidence",
    description: "Read the product-safe verdict, executed schedule, invariant evidence, and repair state for an existing CutoverProof run. The database verifier—not a model—produces the verdict.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string", pattern: "^[A-Za-z0-9][A-Za-z0-9_-]{0,159}$" },
      },
      required: ["run_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: true, untrustedContentHint: true },
    execute: async (raw) => {
      const runId = requiredString(objectInput(raw), "run_id", 160);
      const run = await apiRequest<RunDetail>(`/api/runs/${encodeURIComponent(runId)}`);
      return {
        run_id: run.run_id,
        verdict: run.status_label,
        finding: run.finding,
        invariant_boundary: run.boundary,
        executed_schedule: run.winning_schedule,
        violating_rows: run.evidence_rows,
        repair: run.repair,
        replay: run.replay,
        claims_boundary: run.status === "inconclusive" ? "No counterexample was found within the tested budget; this is not proof of safety." : null,
      };
    },
  },
  {
    name: "open_human_repair_review",
    title: "Open human repair review",
    description: "Open the existing CutoverProof repair-review interface for a verified run. This changes only the visible page; it cannot approve or execute a repair. A named human must approve in the UI.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string", pattern: "^[A-Za-z0-9][A-Za-z0-9_-]{0,159}$" },
      },
      required: ["run_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    execute: async (raw) => {
      const runId = requiredString(objectInput(raw), "run_id", 160);
      const run = await apiRequest<RunDetail>(`/api/runs/${encodeURIComponent(runId)}`);
      if (!run.repair || run.repair.approved) {
        throw new Error("This run does not have a pending allow-listed repair for human review.");
      }
      window.dispatchEvent(new CustomEvent(WEBMCP_OPEN_REPAIR, { detail: { run_id: runId } }));
      return {
        run_id: runId,
        repair_review_opened: true,
        repair_executed: false,
        requires_named_human_approval: true,
      };
    },
  },
];

export function registerCutoverProofTools(): WebMcpRegistration {
  const modelContext = document.modelContext;
  const controller = new AbortController();
  const toolNames = tools.map((tool) => tool.name);
  if (!modelContext || typeof modelContext.registerTool !== "function") {
    return { supported: false, toolNames: [], ready: Promise.resolve(), unregister: () => controller.abort() };
  }
  const ready = Promise.all(
    tools.map((tool) => modelContext.registerTool(tool, { signal: controller.signal })),
  ).then(() => undefined);
  return {
    supported: true,
    toolNames,
    ready,
    unregister: () => controller.abort(),
  };
}

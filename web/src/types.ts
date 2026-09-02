export type View = "overview" | "assessments" | "assessment" | "runs" | "connections" | "settings";

export interface Session { authenticated: boolean; email: string | null; csrf_token?: string | null; }

export interface Health {
  status: string;
  model_configured: boolean;
  execution_boundary: string;
  demo_access_configured: boolean;
}

export interface ScenarioSummary {
  id: string;
  name: string;
  description: string;
  max_candidates: number;
  operation_count: number;
  invariant_count: number;
}

export interface Phase {
  id: string;
  name: string;
  description: string;
  state: "complete" | "pending";
  failed_operation: string | null;
}

export interface RunDetail {
  run_id: string;
  scenario_id: string;
  title: string;
  scenario_name: string;
  scenario_description: string;
  status: "blocked" | "inconclusive" | "failed" | "repair_verified" | "repair_failed";
  status_label: string;
  finding: string;
  error_message: string | null;
  boundary: string | null;
  evidence_rows: Array<Record<string, unknown>>;
  steps: Array<{
    index: number;
    id: string;
    actor: string;
    phase: string;
    description: string;
    duration_ms: number;
    status: string;
  }>;
  phases: Phase[];
  winning_schedule: string[];
  candidates_attempted: number;
  max_budget: number;
  wall_clock_seconds: number;
  approach_id: string;
  model_name: string | null;
  model_calls: number;
  model_tokens: number;
  repair: {
    id: string;
    name: string;
    description: string;
    explanation: string;
    approved: boolean;
    approved_by: string | null;
  } | null;
  replay: { passed: boolean; status: string; duration_ms: number } | null;
  evidence_url: string;
}

export interface RunSummary {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  title: string;
  status: RunDetail["status"];
  status_label: string;
  candidates_attempted: number;
  max_budget: number;
  approach_id: string;
  wall_clock_seconds: number;
  model_name: string | null;
}

export interface JobState {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  stage?: string;
  result?: RunDetail;
  error?: string;
}

export interface ConnectionSummary {
  id: string;
  label: string;
  host: string;
  port: number;
  database: string;
  username: string;
  server_version?: string;
  status: "configured" | "verified";
}

export interface ConnectionsResponse {
  configured: ConnectionSummary;
  ephemeral: ConnectionSummary[];
}

export interface ChangeReviewDraft {
  id: string;
  scenario_id: string;
  contract_name: string;
  objective: string;
  risk_focus: string[];
  status: "awaiting_human_review";
  requested_by: "browser_agent";
  created_at: string;
  human_action: string;
  execution_started: false;
}

export interface WebMcpAvailability {
  supported: boolean;
  ready: boolean;
  toolCount: number;
  error: string | null;
}

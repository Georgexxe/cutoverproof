import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { WEBMCP_REVIEW_CREATED } from "./webmcp";

const scenarios = [{ id: "u1_status_trigger_race", name: "Status Normalization Trigger/Backfill Race", description: "A legacy write races the status backfill.", max_candidates: 8, operation_count: 8, invariant_count: 1 }];

describe("CutoverProof customer workspace", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      let body: unknown = {};
      if (url.endsWith("/api/auth/session")) body = { authenticated: true, email: "engineer@cutoverproof.dev", csrf_token: "test-csrf" };
      else if (url.endsWith("/api/health")) body = { status: "ok", model_configured: true, execution_boundary: "sandbox", demo_access_configured: true };
      else if (url.endsWith("/api/scenarios")) body = scenarios;
      else if (url.endsWith("/api/runs")) body = init?.method === "POST" ? { job_id: "job-1", status: "queued" } : [];
      else if (url.endsWith("/api/connections")) body = { configured: { id: "configured", label: "Configured demo sandbox", host: "localhost", port: 5432, database: "cutoverproof_sandbox", username: "cutover", status: "configured" }, ephemeral: [] };
      else if (url.endsWith("/api/webmcp/contracts/u1_status_trigger_race")) body = {
        id: "u1_status_trigger_race",
        name: "Status Normalization Trigger/Backfill Race",
        objective: "Verify the compatibility window.",
        phase_order: [{ id: "expand", name: "Expand" }, { id: "backfill", name: "Backfill" }, { id: "cutover", name: "Cutover" }],
        declared_operations: Array.from({ length: 8 }, (_, index) => ({ id: `operation_${index}` })),
        invariants: [{ id: "status_consistency" }],
      };
      else if (url.endsWith("/api/webmcp/contracts")) body = scenarios;
      else if (url.endsWith("/api/webmcp/review-drafts")) body = init?.method === "POST" ? {
        id: "draft-in-app",
        scenario_id: "u1_status_trigger_race",
        contract_name: "Status Normalization Trigger/Backfill Race",
        objective: "Inspect the status-normalization contract and prepare a review focused on stale writes during the compatibility window.",
        risk_focus: ["stale_writes", "compatibility_window"],
        status: "awaiting_human_review",
        requested_by: "browser_agent",
        created_at: "2026-09-02T12:00:00Z",
        human_action: "Review and start the sandbox assessment.",
        execution_started: false,
      } : [];
      return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it("opens on a real workspace rather than a preselected result", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Know what’s safe to ship." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CutoverProof home" })).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Run sample" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /New assessment/i })).toBeEnabled();
    expect(screen.queryByText("Prepared judge experience")).not.toBeInTheDocument();
    expect(screen.queryByText("Execution services")).not.toBeInTheDocument();
    expect(screen.queryByText("DO NOT CUT OVER")).not.toBeInTheDocument();
  });

  it("keeps the guided tour separate from an engineer's own assessment", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click((await screen.findAllByRole("button", { name: "Run sample" }))[0]);
    expect(screen.getByRole("dialog", { name: "Guided tour" })).toBeInTheDocument();
    expect(screen.getByText("Status Normalization Trigger/Backfill Race")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Exit tour" }));
    await user.click(screen.getAllByRole("button", { name: "New assessment" })[0]);
    expect(screen.getByRole("dialog", { name: "New assessment" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use sample pack" })).toBeEnabled();
    expect(screen.getByText("No file selected.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guided demo" })).not.toBeInTheDocument();
  });

  it("dismisses the account menu when the engineer clicks elsewhere", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click(await screen.findByRole("button", { name: "Account menu" }));
    expect(screen.getByText("Signed in as")).toBeInTheDocument();
    await user.click(screen.getByRole("heading", { name: "Know what’s safe to ship." }));
    expect(screen.queryByText("Signed in as")).not.toBeInTheDocument();
  });

  it("saves customer assessment defaults from settings", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect(screen.getByRole("heading", { name: "Assessment defaults" })).toBeInTheDocument();
    await user.selectOptions(screen.getByRole("combobox", { name: /Schedules to test/i }), "6");
    await user.click(screen.getByRole("switch", { name: "Open evidence after a run" }));
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(screen.getByText("Preferences saved")).toBeInTheDocument();
  });

  it("turns an agent-created draft into a visible human handoff", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("heading", { name: "Know what’s safe to ship." });
    act(() => {
      window.dispatchEvent(new CustomEvent(WEBMCP_REVIEW_CREATED, { detail: {
        id: "draft-visible",
        scenario_id: "u1_status_trigger_race",
        contract_name: "Status Normalization Trigger/Backfill Race",
        objective: "Verify stale-write compatibility before the production cutover.",
        risk_focus: ["stale_writes", "compatibility_window"],
        status: "awaiting_human_review",
        requested_by: "browser_agent",
        created_at: "2026-09-02T12:00:00Z",
        human_action: "Review and start the sandbox assessment.",
        execution_started: false,
      } }));
    });

    expect(await screen.findByText("Needs your review")).toBeInTheDocument();
    expect(screen.getByText("Not run yet")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Review & run" }));
    expect(screen.getByRole("dialog", { name: "Run assessment" })).toBeInTheDocument();
  });

  it("lets the engineer prepare an agent review directly inside the platform", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /Prepare a review/i }));
    expect(screen.getByRole("dialog", { name: "Prepare a review" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Prepare review" }));

    expect(await screen.findByText("Found contracts")).toBeInTheDocument();
    expect(await screen.findByText("Checked contract")).toBeInTheDocument();
    expect(await screen.findByText("Prepared review")).toBeInTheDocument();
    expect(screen.getByText("Draft ready")).toBeInTheDocument();

    const calls = vi.mocked(fetch).mock.calls;
    expect(calls.some(([input]) => String(input).endsWith("/api/webmcp/contracts"))).toBe(true);
    expect(calls.some(([input]) => String(input).endsWith("/api/webmcp/contracts/u1_status_trigger_race"))).toBe(true);
    expect(calls.some(([input, init]) => String(input).endsWith("/api/webmcp/review-drafts") && init?.method === "POST")).toBe(true);
    expect(calls.some(([input, init]) => String(input).endsWith("/api/runs") && init?.method === "POST")).toBe(false);
  });
});

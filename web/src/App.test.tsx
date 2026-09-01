import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppV2 as App } from "./App";

const scenarios = [{ id: "u1_status_trigger_race", name: "Status Normalization Trigger/Backfill Race", description: "A legacy write races the status backfill.", max_candidates: 8, operation_count: 8, invariant_count: 1 }];

describe("CutoverProof customer workspace", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      let body: unknown = {};
      if (url.endsWith("/api/auth/session")) body = { authenticated: true, email: "engineer@cutoverproof.dev" };
      else if (url.endsWith("/api/health")) body = { status: "ok", model_configured: true, execution_boundary: "sandbox", demo_access_configured: true };
      else if (url.endsWith("/api/scenarios")) body = scenarios;
      else if (url.endsWith("/api/runs")) body = init?.method === "POST" ? { job_id: "job-1", status: "queued" } : [];
      else if (url.endsWith("/api/connections")) body = { configured: { id: "configured", label: "Configured demo sandbox", host: "localhost", port: 5432, database: "cutoverproof_sandbox", username: "cutover", status: "configured" }, ephemeral: [] };
      return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it("opens on a real workspace rather than a preselected result", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Test your first migration" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CutoverProof home" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Take a quick tour" })).toBeEnabled();
    expect(screen.getByRole("button", { name: /New assessment/i })).toBeEnabled();
    expect(screen.queryByText("Prepared judge experience")).not.toBeInTheDocument();
    expect(screen.queryByText("Execution services")).not.toBeInTheDocument();
    expect(screen.queryByText("DO NOT CUT OVER")).not.toBeInTheDocument();
  });

  it("keeps the guided tour separate from an engineer's own assessment", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click(await screen.findByRole("button", { name: "Take a quick tour" }));
    expect(screen.getByRole("dialog", { name: "Guided tour" })).toBeInTheDocument();
    expect(screen.getByText("Status Normalization Trigger/Backfill Race")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Exit tour" }));
    await user.click(screen.getAllByRole("button", { name: "New assessment" })[0]);
    expect(screen.getByRole("dialog", { name: "New assessment" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Load example template" })).toBeEnabled();
    expect(screen.getByText("Load the example or choose a JSON file to continue.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guided demo" })).not.toBeInTheDocument();
  });

  it("dismisses the account menu when the engineer clicks elsewhere", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click(await screen.findByRole("button", { name: "Account menu" }));
    expect(screen.getByText("Signed in as")).toBeInTheDocument();
    await user.click(screen.getByRole("heading", { name: "Test your first migration" }));
    expect(screen.queryByText("Signed in as")).not.toBeInTheDocument();
  });

  it("saves customer assessment defaults from settings", async () => {
    const user = userEvent.setup(); render(<App />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect(screen.getByRole("heading", { name: "Assessment defaults" })).toBeInTheDocument();
    await user.selectOptions(screen.getByRole("combobox", { name: /Candidate budget/i }), "6");
    await user.click(screen.getByRole("switch", { name: "Open technical evidence automatically" }));
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(screen.getByText("Preferences saved")).toBeInTheDocument();
  });
});

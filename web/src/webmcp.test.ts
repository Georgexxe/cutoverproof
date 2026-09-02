import { afterEach, describe, expect, it, vi } from "vitest";
import { registerCutoverProofTools, WEBMCP_REVIEW_CREATED } from "./webmcp";

describe("CutoverProof WebMCP tools", () => {
  afterEach(() => {
    Reflect.deleteProperty(document, "modelContext");
    vi.unstubAllGlobals();
  });

  it("registers five narrow tools with the browser", async () => {
    const registered: Array<{ name: string; execute: (input: unknown) => Promise<unknown> }> = [];
    Object.defineProperty(document, "modelContext", {
      configurable: true,
      value: {
        registerTool: vi.fn(async (tool) => { registered.push(tool); }),
      },
    });

    const registration = registerCutoverProofTools();
    await registration.ready;

    expect(registration.supported).toBe(true);
    expect(registered.map((tool) => tool.name)).toEqual([
      "list_migration_contracts",
      "inspect_migration_contract",
      "create_change_review_draft",
      "read_verified_migration_evidence",
      "open_human_repair_review",
    ]);
    registration.unregister();
  });

  it("creates only a review draft and announces the human handoff", async () => {
    const registered: Array<{ name: string; execute: (input: unknown) => Promise<unknown> }> = [];
    Object.defineProperty(document, "modelContext", {
      configurable: true,
      value: { registerTool: vi.fn(async (tool) => { registered.push(tool); }) },
    });
    const draft = {
      id: "draft-1",
      scenario_id: "u1_status_trigger_race",
      contract_name: "Status rollout",
      objective: "Check the compatibility window before release.",
      risk_focus: ["stale_writes"],
      status: "awaiting_human_review",
      requested_by: "browser_agent",
      created_at: "2026-09-02T12:00:00Z",
      human_action: "Review and start.",
      execution_started: false,
    };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(draft), { status: 201, headers: { "Content-Type": "application/json" } })));
    const received = vi.fn();
    window.addEventListener(WEBMCP_REVIEW_CREATED, received, { once: true });

    const registration = registerCutoverProofTools();
    await registration.ready;
    const tool = registered.find((item) => item.name === "create_change_review_draft");
    const result = await tool!.execute({
      scenario_id: "u1_status_trigger_race",
      objective: "Check the compatibility window before release.",
      risk_focus: ["stale_writes"],
      idempotency_key: "review:release-42",
    }) as { execution_started: boolean; requires_human_action: boolean };

    expect(result.execution_started).toBe(false);
    expect(result.requires_human_action).toBe(true);
    expect(received).toHaveBeenCalledOnce();
    registration.unregister();
  });
});

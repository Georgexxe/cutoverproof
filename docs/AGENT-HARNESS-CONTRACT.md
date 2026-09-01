# Agent Harness Contract

## Purpose

This contract prevents CutoverProof from becoming a script wearing an agent label. It identifies exactly where adaptive reasoning is permitted, what the deterministic system controls, and which evidence must be captured.

## Agent responsibilities

The specialised agent may:

1. Inspect the agent-visible phase/operation catalog and SQL-invariant descriptions.
2. State a concrete hypothesis about a harmful interleaving.
3. Propose a structured schedule using declared operation identifiers.
4. Observe validator, execution, and verifier results.
5. Revise its hypothesis while budget remains.
6. Explain a verified failure using recorded trace identifiers and evidence rows.
7. Select one repair from the permitted repair catalog.

The specialised agent must not:

- See evaluator-only safety labels or seeded failing schedules.
- Invent operations, phases, tables, or verifier results.
- Execute raw shell commands.
- Execute arbitrary SQL.
- Connect to any database except the sandbox through the tool gateway.
- Decide whether an invariant passed.
- Claim safety after budget exhaustion.
- Apply any repair without a recorded human approval.

## Deterministic responsibilities

The harness alone shall:

- Validate scenario and schedule structure.
- Reset and seed PostgreSQL.
- Execute named operations and phase transitions.
- Run SQL assertions.
- Classify infrastructure, execution, verifier, and invariant outcomes.
- Enforce budgets and termination.
- Generate aggregate metrics from raw artifacts.
- Render timelines from traces.
- Apply checked-in repair variants after approval.

## Controlled tools

Tool names may vary, but the semantics must remain narrow.

| Tool | Input | Output | Mutation |
|---|---|---|---|
| `inspect_scenario` | Scenario ID | Agent-visible phases, operations, dependencies, invariant descriptions, budget | None |
| `propose_or_run_schedule` | Ordered declared operations plus hypothesis | Validation result, run ID, execution summary, invariant evidence | Sandbox reset and declared operations only |
| `inspect_trace` | Run ID | Ordered trace and evidence rows | None |
| `propose_repair` | Failed run ID and permitted repair ID | Validated proposal awaiting approval | None |
| `replay_approved_repair` | Failed run ID, repair ID, approval token/event | Before/after replay result | Fresh sandbox only |

Avoid splitting trivial reads into many decorative tools. Tool count does not determine agent quality.

## Candidate schedule contract

Every candidate must include:

- Hypothesis.
- Ordered operation identifiers.
- Optional declared concurrency boundary if supported.
- Expected invariant boundary to inspect.
- Short reason the schedule differs from prior attempts.

The validator shall canonicalize the schedule and reject undeclared operations.

## Budgets and termination

Recommended defaults:

- Maximum candidate executions: 4 in the audited benchmark (configurable up to scenario limits).
- Maximum malformed candidate retries: 2.
- Maximum model-call retries for transient failure: 1.
- Maximum repair proposals: 1 for the hackathon demonstration.
- Stop immediately after the first verified counterexample unless evaluation explicitly requests continued coverage.

Termination reasons must be explicit:

- `verified_counterexample`
- `budget_exhausted_inconclusive`
- `invalid_scenario`
- `agent_error`
- `infrastructure_error`
- `verifier_error`
- `human_approval_declined`
- `repair_replayed`

## Trajectory schema

Each trajectory record must contain enough information for a judge to follow the loop:

- Run ID and step index.
- Timestamp.
- Agent/model/prompt version.
- Agent-visible observation.
- Structured tool request.
- Tool validation result.
- Tool response or error classification.
- Budget before and after the step.
- Retry or revision relationship.
- Human checkpoint event.
- Final termination reason.

Do not serialize hidden evaluator labels, API keys, environment dumps, or unrestricted chain-of-thought. A concise decision rationale and observable tool interaction are sufficient.

## Prompt requirements

The versioned specialised-agent instruction must:

- State the temporal migration objective.
- Tell the agent to search for short, executable schedules rather than produce generic advice.
- Explain that only SQL verifier output determines pass/fail.
- Forbid claims of exhaustive safety.
- Require explicit hypothesis revision after a failed attempt.
- Require operation IDs rather than free-form SQL.
- Describe budget and termination behavior.
- Require evidence-linked explanations.

The one-shot baseline instruction must use the same model, scenario facts, operation vocabulary, and maximum number of candidate schedules, but it must not receive execution feedback before producing its complete candidate list.

## Agent-necessity evidence

The submission may claim an agent contribution only if the checked-in evaluation shows a defensible advantage over at least one non-agent or non-iterative baseline under the same execution budget.

Potential contributions to measure:

- More unsafe scenarios detected.
- Fewer candidate executions before first verified failure.
- Better adaptation after a rejected hypothesis.
- Fewer false alarms on safe controls.
- Evidence-linked diagnosis that matches the deterministic trace.

If a simple heuristic matches the specialised agent, report that result honestly and make the engineering lesson—not inflated superiority—the hot take.

# Emergency Implementation Plan

## Operating rule

Implement the smallest system that satisfies the acceptance criteria. Do not optimize for production generality. Stop adding features when the primary scenario, fair evaluation, clean reproduction, and submission artifacts work.

## Relative schedule

The schedule begins when the coding agent starts. Code should freeze early enough to protect documentation, clean reproduction, trajectory export, video recording, upload, and submission review.

| Window | Objective | Required exit condition |
|---|---|---|
| T+0 to T+30m | Read and restate the frozen scope | Implementation checklist and chosen minimal dependencies recorded; no scope expansion. |
| T+30m to T+4h | Build deterministic core | Clean database reset, primary schema/seed, named operations, known failing schedule, and SQL invariant work without a live model. |
| T+4h checkpoint | Prove the mechanism | U1 known schedule fails for the documented reason and S1 control passes. If not, simplify immediately. |
| T+4h to T+7h | Add approach adapters | One-shot baseline, heuristic/random baseline, and specialised iterative agent all produce validated candidate schedules through the same gateway. |
| T+7h checkpoint | Test agent value | Equal-budget dry run completed; no claims yet. If the agent loses, improve experiment selection once, then report honestly. |
| T+7h to T+10h | Complete benchmark variants | Prioritize U2, U3, and S2 by reuse of existing operations. Save raw artifacts. |
| T+10h to T+12h | Add bounded repair and timeline | U1 human-approved repair replay and static before/after timeline work. |
| T+12h to T+15h | Harden and reproduce | Automated tests, error classifications, secret scan, version pinning, and a clean-environment rehearsal pass. |
| T+15h | Code freeze | Only qualification-gate defects may change code after this point. |
| T+15h onward | Submission production | README, actual changelog, aggregate results, agent trajectories, video, archive/upload, and final checklist. |

If less time remains, cut U2/U3/S2 before cutting U1, S1, fair baseline evidence, trajectories, or clean reproduction.

## Dependency budget

Prefer:

- Python standard library where reasonable.
- One PostgreSQL driver.
- One model SDK or an existing provider abstraction.
- One test runner.
- Docker Compose and PostgreSQL.

Avoid:

- Web frameworks.
- ORM layers.
- Graph databases.
- Queues and caches.
- Frontend build tooling.
- Multiple model providers.
- Dependencies used only for formatting.

Every dependency must be pinned or constrained, licensed appropriately, and documented.

## Milestone 1: Deterministic proof core

Deliverables:

- Disposable PostgreSQL service.
- Primary schema and synthetic fixtures.
- Unsafe and repaired trigger variants.
- Named deterministic operations.
- Known U1 schedule.
- SQL invariant assertion.
- Raw JSON trace.
- One automated test proving U1 fails and S1 passes.

Do not add a model before this milestone passes.

## Milestone 2: Schedule approaches

Deliverables:

- Shared agent-visible scenario view.
- Shared structured schedule validator.
- Seeded heuristic/random approach.
- One-shot same-model approach.
- Specialised iterative approach with feedback.
- Equal candidate budget enforcement.
- Versioned prompts and tool schemas.

The approaches must not contain direct access to expected labels or known schedules.

## Milestone 3: Evidence and repair loop

Deliverables:

- Stable run/artifact identifiers.
- Per-step trajectory logs.
- Failed assertion evidence rows.
- Bounded repair catalog.
- Explicit human approval event.
- Repaired sandbox replay of the same U1 schedule.
- Timeline generated from raw trace.

## Milestone 4: Evaluation

Deliverables:

- Raw runs for every implemented scenario/approach.
- Same-seed stability runs for U1 and S1.
- Aggregate metrics generated from raw data.
- An honest conclusion, including negative results.
- An improvement changelog where every decision points to evidence.

## Milestone 5: Qualification gate

Deliverables:

- Exact prerequisite versions.
- Exact setup and run commands.
- Exact baseline and evaluation commands.
- Expected duration and model cost.
- No secrets or private data.
- Representative trajectories for every agent.
- Video no longer than five minutes.
- Final archive/repository includes everything necessary to reproduce the main result.

## Scope-cut order

If running late, remove in this order:

1. Additional visual styling.
2. U3, then U2, then S2.
3. Secondary metrics.
4. Natural-language causal prose beyond a short evidence-linked explanation.
5. Any optional static linter integration.

Do not remove:

- U1 and S1.
- Deterministic verifier.
- Specialised agent plus at least one fair baseline.
- Raw evidence and trajectories.
- Human-approved U1 repair replay.
- Clean reproduction instructions.

## Definition of done

Implementation is done only when:

- Automated checks pass.
- The complete primary workflow succeeds from a clean environment.
- Claims in README match generated results exactly.
- Timeline matches raw trace.
- No secrets appear in repository or artifacts.
- The implementation agent completes [`../AUDIT-HANDBACK.md`](../AUDIT-HANDBACK.md).


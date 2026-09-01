# CutoverProof — final submission packet

## Submission title

**CutoverProof: Find the ordering that breaks a PostgreSQL migration**

## One-line description

An adversarial agent that executes dangerous migration schedules in a disposable PostgreSQL sandbox and turns verified failures into human-approved, replayable repair evidence.

## Short description

Online database migrations often fail in the compatibility window, not because one SQL statement is invalid. A backfill, an old worker, and a new cutover can each look correct in isolation but corrupt data in one temporal ordering. CutoverProof helps backend and data-platform engineers discover that ordering before production.

Gemini proposes bounded schedules from declared operation IDs. A deterministic gateway validates every proposal, resets an isolated PostgreSQL database, executes the schedule, and asks read-only SQL invariants for the verdict. When a counterexample is verified, the product blocks cutover, shows the exact ordering and violating rows, and lets a named reviewer approve an allow-listed repair for identical-schedule replay.

## The problem

The intended user is a backend or data-platform engineer preparing an online PostgreSQL expand-and-contract migration. Existing review and migration tools are strong at checking individual steps, but weak at testing the compatibility window across old writes, backfills, new reads, and cutover. The result can be stale references, incomplete backfills, or silent inconsistency that appears only under a specific ordering.

The practical bottleneck is not writing more migration prose. It is choosing the few high-value interleavings to execute, producing a trustworthy verdict, and preserving evidence another engineer can replay.

## The solution

1. Import a structured migration pack or load the built-in example.
2. Inspect the schema, seed data, named operations, and read-only invariant before execution.
3. Let the specialised agent choose a candidate ordering and hypothesis within a fixed budget.
4. Execute the candidate against a freshly reset PostgreSQL sandbox.
5. Use SQL assertion rows—not model prose—to decide pass/fail.
6. Show a customer-readable cutover decision plus queryable technical evidence.
7. Require named human approval before applying an allow-listed repair.
8. Replay the identical failing schedule and record whether the repair passed.

## Why an agent is necessary

The schedule space grows combinatorially, while a useful pre-production check must remain fast and bounded. The agent is used for semantic experiment selection: it reads operation meanings, forms a failure hypothesis, chooses an ordering, observes the deterministic trace, and can revise its next proposal. It cannot execute arbitrary SQL or shell commands and never supplies the verdict.

## Architecture

`Engineer → React portal → FastAPI coordinator → Gemini planner → guarded tool gateway → disposable PostgreSQL → SQL invariant verifier → evidence recorder`

- **Reasoning plane:** Gemini receives the visible phase/operation catalog and proposes structured schedules and hypotheses.
- **Control plane:** the gateway enforces declared IDs, schedule validity, and candidate budget.
- **Execution plane:** PostgreSQL resets, seeds, and executes each schedule sequentially.
- **Decision plane:** read-only SQL invariants return zero rows for pass or concrete violating rows for failure.
- **Evidence plane:** sanitized run JSON, agent trajectories, and self-contained HTML timelines preserve every meaningful step.
- **Repair plane:** only checked-in templates are selectable, and replay requires named human approval.

The deployed demo packages React, FastAPI, and an ephemeral PostgreSQL 17 sandbox in one Cloud Run container. Gemini is accessed through Vertex AI application-default credentials.

## Measured improvement

Five checked-in scenarios use seed 42 and the same maximum of four candidate executions. Both model approaches use `gemini-3.1-flash-lite`.

| Approach | Unsafe recall | Safe false alarms | Mean unsafe search effort |
|---|---:|---:|---:|
| Specialised iterative agent | **3/3** | **0/2** | **1.00** |
| One-shot same-model baseline | 2/3 | 0/2 | 2.33 |
| Seeded heuristic explorer | 3/3 | 0/2 | 3.00 |

A verified find costs its candidate index; a valid miss costs `budget + 1`. The result supports earlier semantic selection under a fixed execution budget. It does not prove general migration safety.

## Biggest engineering lesson

The most important improvement was deleting a scenario-aware offline model fallback. It made early evaluation look perfect whenever the provider failed, which meant the score was not honest model evidence. The final adapter fails closed, records provider faults, separates schedule search from repair selection, and keeps invalid or stale experiments instead of laundering them into misses.

**Hot take:** in safety-critical agent systems, the model should choose the next experiment—not decide whether the experiment passed.

## Safety and integrity

- Exact allow-list for the sandbox host, database, and user.
- Production targets refused.
- No arbitrary SQL, shell, filesystem mutation, or network tool for the agent.
- Server-level commands and role/database changes rejected from imported packs.
- Verifier or provider faults cannot become safe results or counterexamples.
- Evaluator labels and known failing schedules withheld from the agent.
- Consequential repair requires a recorded human approval.
- Every repair replay uses the exact failing schedule.
- Secrets are sanitized before trajectories and evidence are written.

## Honest limitations

- Inputs are structured synthetic packs, not arbitrary repository ingestion.
- Schedules are deterministic sequential simulations, not distributed/thread-level concurrency.
- A safe result means only that no counterexample was found within the tested budget.
- The Cloud Run topology is a single-tenant demonstration, not a production multi-tenant design.
- Provider cost is not claimed; calls and token counts are recorded.

## Judge path

1. Open the product URL supplied with the submission.
2. Sign in with the reviewer credentials.
3. Optionally take the four-step product tour.
4. Select **New assessment**, then **Load example template**.
5. Read the JSON in the editor and run with the default four-candidate budget.
6. Open the `DO NOT CUT OVER` result and inspect technical evidence.
7. Review the exact schedule and violating row.
8. Approve the bounded repair under a reviewer name.
9. Confirm `REPAIR VERIFIED IN SANDBOX` after identical-schedule replay.
10. Open Settings to see the customer defaults and immutable safety boundaries.

## Submission artifacts

- Reproduction: `README.md`
- Coding-agent/tool disclosure: `docs/TOOLS-AND-PROVENANCE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Improvement history: `docs/IMPROVEMENT-CHANGELOG.md`
- Benchmark: `docs/BENCHMARK-RESULTS.md`
- Agent/tool trajectories: `artifacts/trajectories/`
- Machine-readable runs: `artifacts/runs/`
- Self-contained audit timelines: `artifacts/timelines/`
- Independent import packs: `examples/video-demo-packs/`
- Final film: `submission/video/CutoverProof_Competition_Demo_FINAL.mp4`
- Captions: `submission/video/CutoverProof_Competition_Demo_FINAL.srt`

## Links to fill after upload

- Public repository: `https://github.com/Georgexxe/cutoverproof`
- Live product: `https://cutoverproof-1021060138341.us-central1.run.app`
- Demo video: `[PUBLIC_VIDEO_URL]`

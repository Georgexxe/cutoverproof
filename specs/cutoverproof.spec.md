# Feature: CutoverProof Hackathon Submission

## Overview and user value

CutoverProof helps a backend or data-platform engineer test an online PostgreSQL migration as a temporal workflow rather than a list of individually valid steps. It turns a suspected migration race into executable evidence: a candidate schedule, deterministic database trace, violated SQL invariant, visual timeline, and human-approved repair replay.

The hackathon version is intentionally bounded. It demonstrates the mechanism on structured synthetic scenarios and does not claim production readiness or exhaustive verification.

## Functional requirements

### FR-001: Load a structured scenario

When a user selects a checked-in scenario, the system shall load its schema setup, migration phases, named operations, SQL invariants, experiment budget, and expected safety label.

### FR-002: Reject incomplete scenarios

When a scenario omits a required phase, operation, invariant, or expected safety label, the system shall stop before database execution and report the missing field without invoking an agent.

### FR-003: Produce candidate schedules

While an evaluation run has remaining budget, when the specialised agent inspects the scenario graph and prior observations, the system shall accept only structured candidate schedules composed of declared operations and phase transitions.

### FR-004: Control agent tools

While an agent run is active, the system shall restrict the agent to read-only scenario inspection, candidate-schedule proposal, deterministic schedule execution, trace inspection, and bounded repair proposal tools.

### FR-005: Execute schedules deterministically

When a valid candidate schedule is submitted, the deterministic harness shall reset the database to the scenario seed, execute the declared operations in the requested order, and record every phase, operation, transaction outcome, and invariant result.

### FR-006: Verify invariants independently

After every configured verification boundary, the system shall execute the scenario's SQL assertions without asking the language model to determine pass or fail.

### FR-007: Identify a verified counterexample

When any SQL assertion returns a failing result, the system shall mark the schedule as a verified counterexample and preserve the database and execution evidence required to replay it.

### FR-008: Respect experiment budgets

While no counterexample has been verified, when the configured candidate limit or wall-clock limit is reached, the system shall terminate the run and report “not found within budget” rather than “safe.”

### FR-009: Run baselines fairly

When evaluation mode is requested, the system shall run the specialised agent and each enabled baseline with the same scenario information, declared experiment budget, random seed where applicable, and deterministic verifier.

### FR-010: Render evidence

When a run completes, the system shall emit a machine-readable result and a human-readable timeline showing the application version, migration phase, operation order, invariant checks, and first verified failure.

### FR-011: Propose bounded repairs

When a verified counterexample exists, the agent may propose a repair only from the declared hackathon repair set: phase reordering, compatibility-trigger activation before backfill, catch-up reconciliation before cutover, or dual-write coverage correction.

### FR-012: Require human approval

While a repair is pending, when replay is requested without an explicit approval flag, the system shall refuse to apply the repair and shall preserve the original run.

### FR-013: Replay an approved repair

When a human approves a bounded repair, the sandbox shall apply it to a fresh disposable database and replay the exact original schedule with the same invariant boundaries.

### FR-014: Capture agent trajectories

When an agent invokes a tool, the system shall record the prompt or instruction version, structured tool request, tool response, retry, observation, termination reason, and any human checkpoint without recording credentials.

### FR-015: Preserve evidence integrity

When a run artifact is written, the system shall associate it with a run identifier, scenario identifier, approach identifier, seed, configuration, start/end timestamps, and application version or commit identifier when available.

## Non-functional requirements

### Reproducibility

- A clean reviewer shall be able to run setup, advanced solution, baselines, and evaluation using exact documented commands.
- The primary scenario shall produce the same pass/fail invariant outcome across three consecutive runs with the same seed.
- All synthetic fixtures, scenario definitions, prompts, and evaluation scripts shall be checked in.
- No successful run shall depend on a developer's local files or signed-in browser session.

### Performance and budget

- The primary end-to-end demonstration should complete within five minutes on a normal laptop after dependencies are available.
- The default specialised-agent experiment budget shall be no more than eight candidate schedules.
- The implementation shall expose model-call count and approximate cost when an external model is used.
- A model timeout shall terminate or retry within a documented bounded policy rather than hanging indefinitely.

### Security and ethics

- The system shall operate only against the disposable sandbox database supplied by the project.
- The project shall use synthetic data and shall contain no credentials, PII, production connection strings, or customer records.
- The agent shall not receive a general shell, arbitrary SQL mutation, network, or filesystem-write tool.
- A repair shall not be applied without an explicit human approval event.
- Logs shall redact configured secret environment-variable values.

### Reliability

- Database reset shall occur before every candidate schedule.
- A failed reset, SQL error, agent-output validation error, or verifier error shall be distinguished from a verified business-invariant failure.
- A safe scenario shall never be labelled unsafe solely because infrastructure failed.

### Maintainability

- Agent prompts and tool schemas shall be versioned files.
- Scenario data shall be separate from orchestration logic.
- Deterministic executor tests shall not require a live model.
- The README shall distinguish pre-existing dependencies from competition work.

### Usability

- The result shall lead with verdict, scenario, approach, schedules tried, first failing boundary, and replay command.
- “No counterexample found within budget” shall never be displayed as “safe.”

## Acceptance criteria

### AC-001: Primary unsafe scenario is reproduced

Given a clean PostgreSQL sandbox and the primary trigger/backfill scenario
When the known failing schedule is executed
Then the status-consistency SQL assertion fails at the documented boundary
And the trace names the exact operations that preceded the failure.

### AC-002: Specialised agent produces executable evidence

Given the primary scenario without the known schedule disclosed in its agent prompt
When the specialised agent runs within its candidate budget
Then it proposes a schema-valid schedule
And the deterministic harness either verifies a failure or records each rejected hypothesis
And the final result does not rely on model self-evaluation.

### AC-003: Safe control does not produce a false alarm

Given the corrected trigger and phase ordering
When the same workload family is evaluated
Then every executed SQL assertion passes
And the result is “no counterexample found within budget,” not an unconditional proof of safety.

### AC-004: Baseline budgets are equal

Given a scenario and fixed candidate budget
When the specialised agent, one-shot model baseline, and heuristic/random baseline are evaluated
Then each receives the same scenario facts and verifier
And the output records the number of schedules attempted and wall-clock duration for each.

### AC-005: Repair requires approval

Given a verified counterexample and proposed repair
When replay is requested without approval
Then no repaired migration is applied
And the result records a blocked human checkpoint.

### AC-006: Approved repair is replayable

Given a verified counterexample and approved bounded repair
When the repair replay runs against a fresh sandbox
Then it executes the identical schedule and invariant boundaries
And the before/after results appear together in the run artifact.

### AC-007: Clean reproduction succeeds

Given a reviewer with the documented prerequisite versions and no project-specific state
When they follow the reproduction guide
Then they can run the primary solution, baselines, and evaluation
And locate the generated trace and timeline at documented paths.

### AC-008: Agent trajectory is inspectable

Given a completed advanced run
When a reviewer opens its trajectory artifact
Then they can follow the agent instruction, tool requests, tool responses, observations, retries, human checkpoint, and termination reason without encountering a secret.

## Error handling

| Error condition | Required classification | Required behavior |
|---|---|---|
| Invalid scenario structure | Input error | Stop before agent/database work and name invalid fields. |
| Undeclared operation in schedule | Agent-output error | Reject the schedule, record the rejection, and count it according to the documented budget policy. |
| PostgreSQL unavailable | Infrastructure error | Stop the run, preserve logs, and do not classify scenario safety. |
| SQL operation fails unexpectedly | Execution error | Record SQL state and operation; do not treat it as an invariant counterexample unless the scenario declares that error as the invariant. |
| SQL assertion cannot execute | Verifier error | Mark evaluation invalid and stop claims for that scenario. |
| Model timeout or malformed response | Agent error | Apply bounded retry policy, record it, then terminate cleanly if exhausted. |
| Budget exhausted | Inconclusive result | Report “not found within budget.” |
| Repair requested without approval | Human-checkpoint block | Refuse mutation and provide the approval instruction. |
| Artifact write fails | Evidence error | Mark run incomplete and exclude it from aggregate metrics. |

## Implementation checklist

### Deterministic core

- [ ] Define structured scenario schema and validation.
- [ ] Provision disposable PostgreSQL.
- [ ] Implement reliable reset and seed behavior.
- [ ] Implement named operations and phase transitions.
- [ ] Implement deterministic schedule execution.
- [ ] Implement SQL assertion verification.
- [ ] Emit machine-readable run artifacts.

### Agent layer

- [ ] Version the specialised planner instruction.
- [ ] Define narrow structured tool schemas.
- [ ] Validate every candidate schedule before execution.
- [ ] Enforce experiment and retry budgets.
- [ ] Capture representative trajectories.
- [ ] Add bounded repair proposals and human approval.

### Evaluation

- [ ] Implement primary unsafe scenario.
- [ ] Implement two additional unsafe variants where time permits.
- [ ] Implement two safe controls where time permits.
- [ ] Implement one-shot LLM baseline.
- [ ] Implement heuristic/random baseline.
- [ ] Run equal-budget evaluation and save raw results.
- [ ] Report detection and false-alarm results without embellishment.

### Presentation and submission

- [ ] Generate a visual timeline for the primary failure.
- [ ] Document exact clean-environment commands.
- [ ] Write the improvement changelog from actual experiments.
- [ ] Record a five-minute-or-shorter solution video.
- [ ] Package code, reproduction guide, video link, and agent trajectories.

## Out of scope

See [`../00-FROZEN-DECISION.md`](../00-FROZEN-DECISION.md). Any implementation task not required by the acceptance criteria is out of scope unless a human explicitly changes the frozen decision.

## Open questions delegated to the implementation agent

- Choose the smallest compatible language/model SDK combination already available to the builder.
- Record the choice and exact versions; do not introduce a framework solely for prestige.
- If external model access is unavailable, stop and report the missing dependency instead of silently replacing the advanced agent with hard-coded output.


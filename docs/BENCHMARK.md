# Evaluation and Benchmark Plan

> This is the pre-implementation plan. The authoritative executed configuration and results are in [`BENCHMARK-RESULTS.md`](BENCHMARK-RESULTS.md). The audited matrix used budget 4, not the aspirational budget 8 described below.

## Objective

Demonstrate whether a specialised, feedback-driven agent selects productive migration schedules more effectively than fair baselines, while relying on the same deterministic executor and SQL verifier.

The benchmark is not intended to establish industry-wide performance. It is a small, transparent hackathon evaluation with raw evidence.

## Scenario matrix

| ID | Expected evaluator label | Failure mechanism | Priority |
|---|---|---|---|
| U1 | Unsafe | Payment trigger changes legacy status after the row has been backfilled but before compatibility coverage | P0 |
| U2 | Unsafe | Legacy cancellation changes text status after its backfill batch, leaving the new identifier stale | P1 |
| U3 | Unsafe | New-only read cutover begins before backfill and reconciliation complete | P1 |
| S1 | Safe within tested schedules | Compatibility trigger active before backfill; catch-up and invariant gate precede cutover | P0 |
| S2 | Safe within tested schedules | Compatibility read path remains active until completed backfill and verification | P1 |

Evaluator labels must be excluded from agent-visible input.

If time forces a reduction, U1 and S1 are mandatory. Do not claim broad measured improvement from a two-scenario demonstration; label it a proof of concept.

## Approaches

### A0: Static context baseline

Run the selected migration linter or documented static checks, if practical. This is contextual evidence, not the strongest baseline, because static checks are not expected to execute temporal schedules.

### A1: One-shot LLM baseline

- Same model as advanced approach.
- Same agent-visible scenario facts and operation vocabulary.
- One prompt, no execution feedback.
- May propose up to eight candidate schedules in one response.
- Candidates run through the same validator/executor/verifier.

### A2: Heuristic/random explorer

- No language model.
- Generates valid schedules using documented phase-boundary heuristics or seeded random selection.
- Same maximum of eight candidate executions.
- Same schedule-length limit and verifier.
- Seed recorded.

### A3: Specialised iterative agent

- Same model facts and operation vocabulary as A1.
- May inspect deterministic feedback after each candidate.
- Maximum of eight candidate executions.
- Must revise its hypothesis based on recorded observations.

## Fairness controls

- Identical scenario assets except hidden evaluator label.
- Identical executor, verifier, database version, reset strategy, and hardware environment.
- Identical maximum candidate executions.
- Record both wall-clock and model calls; do not conceal an approach's larger cost.
- Use fixed seeds for reproducible random baselines.
- Do not manually correct malformed advanced schedules without applying the documented policy.
- Preserve all runs, including failures and removed experiments.
- The timeline renderer must consume raw traces for every approach.

## Metrics

### Primary

- **Unsafe detection recall:** unsafe scenarios with at least one deterministically verified counterexample divided by total unsafe scenarios.
- **Harmful false-approval rate:** unsafe scenarios reported as no issue without the required “within budget” qualification.
- **Safe-control false-rejection rate:** safe controls with a deterministically verified violation caused by the approach rather than the declared scenario.
- **First-counterexample efficiency:** median candidate executions before first verified failure.

### Secondary

- Valid-schedule rate.
- Wall-clock duration.
- Model calls and approximate model cost.
- Verified repair replay success on U1.
- Explanation evidence fidelity: whether cited operations and invariant rows exist in the trace. This should be checked mechanically where possible.

## Result vocabulary

Permitted:

- `verified_counterexample_found`
- `no_counterexample_found_within_budget`
- `invalid_run`
- `repair_replay_passed`
- `repair_replay_failed`

Prohibited:

- `safe` unless carefully scoped to the exact tested schedule set.
- `proved safe`.
- `all bugs found`.

## Minimum win conditions

The strongest claim is allowed only if all are true:

1. U1 is detected by the specialised agent with executable evidence.
2. S1 does not produce a false counterexample.
3. At least one fair baseline is weaker on detection or first-counterexample efficiency under equal budget.
4. The result is reproducible across three same-seed runs.
5. The approved U1 repair passes replay of the original schedule.

The desired full target is 3/3 unsafe detection and 0/2 safe false rejections, but actual results must be reported even if lower.

## Kill condition

If A2's simple heuristic/random exploration matches or beats A3 on all checked-in scenarios under the same budget, the submission must not claim that semantic agent experiment selection is superior. Options then are:

- Improve the specialised selection mechanism using genuine scenario semantics and rerun.
- Present the negative result as an engineering insight while retaining the deterministic product value.
- Reduce claims rather than manipulating scenarios or budgets.

## Required evidence artifacts

- Per-run configuration.
- Per-run trajectory for model approaches.
- Candidate schedules and validation outcomes.
- Raw ordered executor traces.
- SQL assertion identifiers and evidence rows.
- Aggregate metrics generated from raw artifacts.
- Three-run stability output for U1 and S1.
- Before/after U1 repair replay.
- Improvement changelog referencing artifact paths.

## Changelog experiments to capture

The final changelog must reflect reality, but expected useful entries include:

1. Deterministic known-schedule baseline establishes the failure.
2. Random or heuristic schedule exploration establishes the non-agent baseline.
3. One-shot LLM proposes schedules without feedback.
4. Specialised iterative planner receives tool feedback.
5. One attempted feature is removed because it did not improve evidence or endangered reproducibility.

Do not fabricate an iteration that did not occur.

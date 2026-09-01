# Audited benchmark results

## Configuration

- Generated: 2026-08-31 00:20 UTC
- Scenarios: U1, U2, U3, S1, S2
- Candidate-execution budget: 4 per scenario and approach
- Seed: 42
- Model for A1 and A3: `gemini-3.1-flash-lite`
- PostgreSQL: 16.15 in the checked-in Docker Compose sandbox
- Evaluator labels and known failing schedules: excluded from agent-visible input
- Repair generation: disabled during benchmark so it does not distort experiment-selection cost

## Results

| Approach | Unsafe recall | Safe false alarms | Mean unsafe effort* | Wall clock | Model calls | Tokens | Invalid runs |
|---|---:|---:|---:|---:|---:|---:|---:|
| A3 specialised iterative agent | 3/3 | 0/2 | 1.00 | 108.94 s | 15 | 15,678 | 0 |
| A1 one-shot same-model baseline | 2/3 | 0/2 | 2.33 | 57.04 s | 5 | 3,122 | 0 |
| A2 seeded heuristic explorer | 3/3 | 0/2 | 3.00 | 15.26 s | 0 | 0 | 0 |

\* A find costs its candidate index. A valid miss costs `budget + 1` (5). This metric penalizes misses while retaining search efficiency.

## What the result supports

- A3 found all three checked-in unsafe mechanisms and produced no false counterexample on either control.
- A3 found each unsafe mechanism on its first executed candidate.
- The one-shot baseline missed U1 within four candidates.
- The heuristic matched A3's recall but required more candidate executions. Therefore the evidence supports more efficient semantic experiment selection, not a claim that heuristics cannot solve these fixtures.
- No result proves general migration safety or production readiness.

## Integrity rules

An agent, infrastructure, execution, verifier, or scenario error makes the relevant coverage metric `INVALID`; it is never counted as a miss or pass. Resume mode reuses only artifacts matching approach, scenario, budget, seed, and model. Replaced results are copied into `artifacts/invalidated/` before rerun.

The aggregate is generated from [`../artifacts/evaluation/benchmark_results.json`](../artifacts/evaluation/benchmark_results.json). Current per-run evidence is under `artifacts/runs/`; agent/tool trajectories are under `artifacts/trajectories/`.

## Cost and quota

The harness records calls and provider-reported tokens but does not calculate pricing, so cost remains unclaimed. Free-tier quotas and model availability changed during audit; the failed attempts and provider errors are retained as improvement evidence. A full clean rerun may require billing or multiple quota periods. `--resume` prevents valid cells from being repeated.

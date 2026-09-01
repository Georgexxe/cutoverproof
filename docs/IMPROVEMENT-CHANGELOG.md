# Evidence-linked improvement changelog

This is the factual engineering chronology. It includes failed approaches because the competition asks each iteration to connect to evidence.

## 1. Deterministic harness and fixtures

Built a PostgreSQL reset/seed/execute/verify loop, three unsafe temporal fixtures, two safe controls, equal-budget approaches, JSON evidence, and HTML timelines. Known schedules were used only by deterministic regression tests and kept out of `ScenarioView`.

Evidence: `tests/test_deterministic_core.py`, `tests/test_scenario_loader.py`, and the current `artifacts/runs/` files.

## 2. Removed the scenario-aware “offline model” fallback

The initial implementation silently returned hard-coded schedules for known scenario IDs whenever a model call failed. Its 3/3 benchmark was therefore not model evidence. Audit removed that path completely: production A1/A3 now require a live provider and emit `agent_error` on failure. Unit tests use an explicitly test-only scripted double.

Why it mattered: the old README's 100% agent claim was invalid. This was the most important correction.

Evidence: `src/agent/llm_client.py`, `tests/fakes.py`, and `tests/test_safety_and_evidence.py`.

## 3. Failed closed on retired models and provider faults

The first honest call showed `gemini-2.5-flash` unavailable to new users and directed migration to a current model. Later runs exposed 504 timeouts, daily quota exhaustion, and truncated JSON. The adapter now records provider/model/error, uses JSON output mode, sets a 60-second timeout, retries once only for transient or malformed output, and never retries permanent authentication/not-found/daily-quota failures.

Evidence: archived run JSON under `artifacts/invalidated/`; current run metadata under `artifacts/runs/`.

## 4. Made destructive and consequential actions explicit

Database reset now refuses every target except the allow-listed local `cutoverproof_sandbox` database and `cutover` user. Credential-bearing URLs are not echoed. Repair replay is disabled by default and requires `--approve-repair`; the approver and timestamp are recorded. Benchmark mode never auto-approves a repair.

Evidence: `src/executor/db.py`, `src/repair/approval.py`, `tests/test_safety_and_evidence.py`, and `artifacts/runs/run_a3_u1_status_trigger_race_42_approved_repair.json`.

## 5. Corrected evidence rendering and aggregation

The initial timeline selected the first trace even when a later candidate was the counterexample and depended on Tailwind's CDN. It now selects the verified trace, escapes rendered fields, and embeds CSS. Aggregate recall previously treated invalid model runs as misses; invalid coverage now invalidates the metric and is shown separately.

Evidence: `src/report/timeline.py`, `src/coordinator/cli.py`, and `tests/test_safety_and_evidence.py`.

## 6. Added resumable, integrity-preserving evaluation

Full adaptive safe-control searches can exceed free-tier quotas. `evaluate --resume` reuses only matching valid artifacts and archives invalid or stale JSON/trajectory files before replacement. This restored feature improved reproducibility without changing budgets or hiding failures.

Evidence: `src/coordinator/cli.py` and `artifacts/invalidated/`.

## 7. Fixed the schedule/repair prompt contract

Flash Lite revealed that the schedule-search prompt advertised `propose_repair` before any verified failure—even on controls with no repair. The model followed that contradictory instruction and produced invalid runs. Schedule search and post-verification repair now use separate prompts. Unsupported/malformed planner output receives bounded feedback. Duplicate schedules are valid but wasteful and therefore consume candidate budget rather than granting free retries.

Evidence: archived safe-control failures, `src/agent/specialised_agent.py`, and `test_specialised_agent_recovers_from_premature_repair_action`.

## 8. Replaced the misleading efficiency metric

“Average attempts among successful detections” rewarded approaches that missed hard cases. The primary efficiency value now scores a valid miss as `budget + 1`. Under the final matrix: A3 = 1.00, A1 = 2.33, A2 = 3.00.

Evidence: `artifacts/evaluation/benchmark_results.json` and [`BENCHMARK-RESULTS.md`](BENCHMARK-RESULTS.md).

## 9. Replaced the raw-evidence demo with a customer workflow

The first visible interface was a generated evidence timeline: useful for audit, but too dense to serve as the product. A React/FastAPI portal now leads with the migration decision, plain-language failure, phase conflict, and recommended action. It runs real assessments, polls background jobs, exposes readable technical evidence, records named approval, replays the exact failing schedule, and preserves product run history. Baseline scores and chat comparisons were removed from the customer UI and kept in evaluation artifacts.

The portal also fixed two decision-integrity defects found during browser QA: an agent error can no longer appear as a bounded safe miss, and an inconclusive result uses an amber warning state with explicit “not proof of safety” copy.

Evidence: `web/src/App.tsx`, `src/api/`, `tests/test_web_api.py`, `web/src/App.test.tsx`, and `design-qa.md`.

## 10. Turned the result viewer into a judge-testable product

The portal now starts at an authenticated workspace rather than silently opening a preselected result. A judge can launch the supplied PostgreSQL demonstration, browse assessment packs and run history, test an exact allow-listed disposable connection, or import a bounded JSON pack containing their own schema, seed, operations, and SQL invariant. Imported SQL is screened for server-level escape/admin commands; connection credentials are memory-only and never enter evidence artifacts. The guided U1 flow, custom inventory pack, evidence modal, named approval, and identical-schedule repair replay were all exercised through the browser against the live API.

Evidence: `src/api/app.py`, `src/api/schemas.py`, `src/scenarios/loader.py`, `examples/custom_assessment_pack.json`, `web/src/App.tsx`, and the 2026-08-31 browser QA pass.

## 11. Split judge demonstration from engineer import and added product identity

The prepared status-normalization proof now has a dedicated “Run guided demo” entry with a fixed four-candidate budget, an explicit three-step explanation, and the sandbox boundary visible before execution. “New assessment” is now exclusively the bring-your-own-migration path, with example-template loading and JSON upload. A generated CutoverProof migration-path mark replaces the generic shield across authentication and workspace surfaces.

Evidence: `web/src/App.tsx`, `web/src/App.test.tsx`, `web/src/assets/cutoverproof-mark.png`, `web/design/implementation-product-home-final.png`, and `web/design/implementation-guided-demo-final.png`.

## 12. Rebuilt the entry experience around the backend engineer

The signed-in product now opens on a quiet Workspace with exactly two choices: **Run demo** and **New assessment**. The former is a four-step coach-mark tour over the real interface before it launches the live U1 run; the latter remains the bounded JSON migration-pack import. Judge, hackathon, execution-target, and service-readiness copy was removed from the customer journey. Connection management and internal safe-control fixtures no longer compete with the main task. Account popovers dismiss on outside click, the assessment library is a compact three-sample list, and the CP mark now leads a deliberately quieter wordmark.

Evidence: `web/src/App.tsx`, `web/src/styles.css`, `web/src/App.test.tsx`, `web/design/redesign-2026-08-31/redesign-comparison.png`, and `design-qa.md`.

## Removed/deferred features

- Removed: scenario-aware offline fallback, external CSS dependency, automatic repair approval.
- Deferred: arbitrary repository ingestion, general repair synthesis, counterexample minimization, true concurrent transaction scheduling, and production database connectivity. Structured JSON assessment-pack import is implemented; it is deliberately narrower than repository ingestion.
- Reason: each would expand qualification and reproducibility risk more than it would improve the remaining rubric evidence before deadline.

## 13. Removed demo residue and added engineer-controlled defaults

The final customer build starts as a fresh product, not a pre-populated hackathon dashboard. Home contains one primary action and one optional tour. Assessments shows an honest empty state until the signed-in engineer runs something. The former duplicate Runs page was removed. Settings now persists the default candidate budget and whether technical evidence should open after a failed assessment; immutable execution safeguards remain visible but cannot be weakened.

Evidence: `web/src/App.tsx`, `web/src/app.css`, `web/src/App.test.tsx`, and browser QA at desktop and 390-by-844 mobile viewports.

## 14. Proved the import path with independent packs

The built-in inventory example and three separate JSON packs were all exercised through the customer import path. They cover a status-trigger/backfill race, a legacy update after backfill, and cutover before backfill completion. Each produced a real PostgreSQL counterexample and a `DO NOT CUT OVER` decision. The files are checked in under `examples/video-demo-packs/`; copies are supplied separately for the recorded demo.

Evidence: `artifacts/imported_scenarios/`, `artifacts/runs/run_a3_*_upload_42.json`, `artifacts/trajectories/run_a3_*_upload_42_trajectory.json`, and `examples/video-demo-packs/`.

## 15. Packaged the product for Cloud Run without relaxing the database guard

The final image serves the React build and FastAPI API together and starts PostgreSQL 17 inside the same disposable Cloud Run instance. The sandbox still uses the exact allow-listed `cutover` identity and `cutoverproof_sandbox` database, resets between candidates, refuses production targets, limits the service to one instance and one concurrent request, and authenticates Gemini through Vertex AI application-default credentials rather than embedding a key.

Evidence: `Dockerfile`, `scripts/start-cloud-run.sh`, `src/agent/llm_client.py`, `src/executor/db.py`, `tests/test_safety_and_evidence.py`, and `docs/CLOUD-RUN.md`.

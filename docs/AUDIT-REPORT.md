# Independent implementation audit

## Verdict

The implementation is a credible, runnable submission. The deterministic core, live-model boundary, explicit approval gate, guarded database reset, current benchmark, customer portal, Cloud Run release, and live repair replay were independently exercised. It is not represented as a production multi-tenant service.

## Material findings corrected

| Severity | Finding in initial handback | Correction |
|---|---|---|
| Critical | Silent scenario-aware fallback returned known winning schedules and was reported as model performance. | Removed from production; missing/failed live models produce `agent_error`. |
| High | Repair replay was effectively auto-approved by default. | Default is no replay; `--approve-repair` records approver and timestamp. |
| High | `DROP SCHEMA public CASCADE` lacked a production-target guard. | Reset is limited to local host/service, exact database, and exact user. |
| High | Benchmark counted failed model runs as misses and could still print recall. | Any invalid coverage makes the metric `INVALID`; invalid count is explicit. |
| Medium | Timeline used external Tailwind and could render the wrong candidate trace. | CSS is embedded; verified trace is selected and escaped. |
| Medium | Scenario IDs/files could escape the scenario root. | IDs and referenced paths are validated and contained. |
| Medium | Same run ID allowed repair evidence to be overwritten by benchmark mode. | Approved repair uses a separate `_approved_repair` run ID. |
| Medium | Provider/version errors, quota, malformed JSON, and duplicate planner output were poorly handled. | Bounded timeout/retry, provider metadata, resume archive, split prompts, and explicit duplicate-budget policy added. |
| Medium | README and handback claimed 18 tests, retired model versions, false cost, and invalid 100% results. | Replaced with exact tested versions, 23 tests, and generated audited results. |

## Verification performed

- `python -m compileall -q src tests`
- `python -m pytest -q` → 38 passed
- React workflow tests → 4 passed; TypeScript check and Vite production build passed
- guarded `test-db` against project PostgreSQL
- deterministic known-failure and safe-control repetitions
- real Gemini 3.1 Flash Lite A1/A3 benchmark at budget 4
- explicit U1 repair approval and identical-schedule replay → `repair_replay_passed`
- public Cloud Run health, login, fresh JSON import, Vertex planning, PostgreSQL verdict, evidence retrieval, and repair replay on revision `cutoverproof-00007-mrc`
- model-free failure, path containment, production DB rejection, secret redaction, and self-contained timeline regressions

Environment checked: Python 3.12.13, Docker 29.4.0, PostgreSQL 16.15, psycopg 3.3.4, Pydantic 2.13.5, pytest 9.1.1, Rich 15.0.0, google-genai 2.20.0, OpenAI SDK 3.6.0.

## Residual risks and limitations

1. The benchmark has five synthetic fixtures in one schema-migration family. It demonstrates the mechanism, not broad external validity.
2. Schedules simulate interleavings by sequentially executing declared operations; thread-level concurrency, isolation anomalies, and distributed timing are out of scope.
3. Current invariants execute at schedule end. The data model does not yet expose multiple configured checkpoints.
4. Gemini model names, free quotas, and availability can change. The CLI exposes `--model`; complete reruns may require a billed key.
5. Provider seeds are best-effort. SQL outcomes are deterministic; model text is not guaranteed identical.
6. Approximate provider cost is intentionally unclaimed because pricing calculation is not implemented.
7. Cloud Run job state and its embedded PostgreSQL database are intentionally ephemeral; a production design requires durable queues, storage, and isolated database workers.
8. The public source and live product are published. The recorded film still requires a YouTube URL, and the missed deadline requires the organizers to accept a discretionary late review.

## Feature decision

Do not restore general migration ingestion, counterexample minimization, arbitrary repair synthesis, or true concurrency before submission. The highest-value restored capability was resumable evaluation with invalid-artifact preservation. Remaining time should go to clean-package rehearsal, video, and submission verification.

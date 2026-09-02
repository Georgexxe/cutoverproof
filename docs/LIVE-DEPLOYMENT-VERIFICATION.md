# Live deployment verification

The base public workflow was exercised end to end on 2026-09-01. The WebMCP release was deployed and smoke-tested on 2026-09-02. This is a live-service verification record, not a replacement for the checked-in benchmark.

## Release identity

- Public product: `https://cutoverproof-1021060138341.us-central1.run.app`
- GitHub source: `https://github.com/Georgexxe/cutoverproof`
- Source release: `60021ad`
- Cloud Build: `6ca78953-8d49-4d05-9a9b-f7a5bb9a1405` (`SUCCESS`)
- Cloud Run revision: `cutoverproof-00008-4sk` (100% traffic)
- Container digest: `sha256:39ef85f1031d4571654903585ddb230f58f258ce43eaa7500b64a7087b7b601e`
- Rollback revision: `cutoverproof-00007-mrc`
- Runtime service account: `cutoverproof-runner@project-ca8af2fe-5aff-496a-bd8.iam.gserviceaccount.com`

## WebMCP release verification — 2026-09-02

1. `GET /api/health` returned `status: ok` and `model_configured: true`.
2. The public login page rendered in the in-app browser with no console errors.
3. The public OpenAPI exposed `/api/webmcp/contracts`, `/api/webmcp/contracts/{scenario_id}`, and `/api/webmcp/review-drafts`.
4. The response headers included `Permissions-Policy: tools=(self)` and the expected restrictive content-security policy.
5. Secret-backed reviewer sign-in succeeded.
6. Authenticated contract discovery returned 11 bounded migration contracts.
7. Creating the idempotent deployment-smoke review for `u1_status_trigger_race` returned `awaiting_human_review` and `execution_started: false`.
8. A fresh four-candidate assessment of `u1_status_trigger_race` completed through the deployed API and live Vertex model.
9. `gemini-3.1-flash-lite` proposed a candidate; PostgreSQL executed it and the independent invariant returned one violating row.
10. The release returned `DO NOT CUT OVER` after candidate 1 and offered the allow-listed repair.
11. The named reviewer `Deployment Verification` approved the bounded sandbox replay.
12. The identical failing schedule returned `REPAIR VERIFIED IN SANDBOX` with `repair_replay_passed`.

The API and execution boundary are verified on the final release. Interactive discovery of all five page-registered WebMCP tools in the judge browser remains part of the manual reviewer protocol.

### Final-release result summary

```json
{
  "run_id": "run_a3_u1_status_trigger_race_42",
  "initial_verdict": "DO NOT CUT OVER",
  "candidates_attempted": 1,
  "evidence_rows": 1,
  "approved_run_id": "run_a3_u1_status_trigger_race_42_approved_repair",
  "final_verdict": "REPAIR VERIFIED IN SANDBOX",
  "replay_status": "repair_replay_passed"
}
```

## Full public workflow exercised — 2026-09-01

1. `GET /api/health` returned `status: ok` with a configured live model and customer portal.
2. Reviewer sign-in succeeded using the secret-backed Cloud Run credential.
3. A fresh customer JSON pack, `u1_status_trigger_race_release_verify_r7`, was imported and submitted to the specialised agent with seed 42 and a four-candidate budget.
4. `gemini-3.1-flash-lite` proposed a candidate through Vertex AI.
5. PostgreSQL executed the declared schedule and the independent SQL invariant returned a violating row.
6. The product returned `DO NOT CUT OVER` after candidate 1 and proposed the allow-listed compatibility-trigger repair.
7. A named human approved the repair.
8. PostgreSQL replayed the identical failing schedule with the repair and returned `REPAIR VERIFIED IN SANDBOX` / `repair_replay_passed`.

## Sanitized result summary

```json
{
  "run_id": "run_a3_u1_status_trigger_race_release_verify_r7_42",
  "initial_verdict": "DO NOT CUT OVER",
  "candidates_attempted": 1,
  "model": "gemini-3.1-flash-lite",
  "approved_run_id": "run_a3_u1_status_trigger_race_release_verify_r7_42_approved_repair",
  "final_verdict": "REPAIR VERIFIED IN SANDBOX",
  "replay_status": "repair_replay_passed"
}
```

No password, access token, model credential, or database credential is stored in this record.

# Live deployment verification

The public deployment was exercised end to end on 2026-09-01. This is a live-service verification record, not a replacement for the checked-in benchmark.

## Release identity

- Public product: `https://cutoverproof-1021060138341.us-central1.run.app`
- GitHub source: `https://github.com/Georgexxe/cutoverproof`
- Cloud Build: `fa3aee25-644d-44f8-ada0-adca5a3e6b34` (`SUCCESS`)
- Cloud Run revision: `cutoverproof-00007-mrc` (100% traffic)
- Container digest: `sha256:151a50328c402532cf54e924003b916ef953d698f6f9d929ea41bfb0a07984a6`
- Runtime service account: `cutoverproof-runner@project-ca8af2fe-5aff-496a-bd8.iam.gserviceaccount.com`

## Public workflow exercised

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

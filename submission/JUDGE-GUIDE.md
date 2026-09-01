# CutoverProof judge guide

## Live product

- URL: `https://cutoverproof-1021060138341.us-central1.run.app`
- Reviewer credentials are supplied in the submission email; no secret is committed to this repository.

## Fastest complete evaluation path

1. Sign in.
2. Select **Take a quick tour** if you want the product map; exit after the fourth coach mark.
3. Select **New assessment**.
4. Select **Load example template**. The full JSON remains visible and editable.
5. Select **Run assessment**.
6. Open **Inspect technical evidence** on the completed decision.
7. Check the three-step schedule and the `status = paid`, `status_id = pending` evidence row.
8. Close evidence, select **Review & approve repair**, enter your name, and approve.
9. Confirm the identical schedule reports **REPAIR VERIFIED IN SANDBOX**.

## Repository-first fallback

If the model provider or Cloud Run instance is temporarily unavailable, the complete executed result is checked in:

- Run: `artifacts/runs/run_a3_u1_status_trigger_race_42_approved_repair.json`
- Trajectory: `artifacts/trajectories/run_a3_u1_status_trigger_race_42_approved_repair_trajectory.json`
- Visual timeline: `artifacts/timelines/run_a3_u1_status_trigger_race_42_approved_repair_timeline.html`

This fallback is evidence from a real prior execution. It is not used to fabricate a live model result.

## Additional import cases

The `examples/video-demo-packs/` directory contains three distinct packs that exercise the same customer import path:

- `01-status-trigger-backfill-race.json`
- `02-legacy-update-after-backfill.json`
- `03-cutover-before-backfill-complete.json`

Each has a corresponding run and agent trajectory under `artifacts/`.

## Important interpretation

`DO NOT CUT OVER` means a concrete invariant violation was executed and verified. A clean bounded search means only “no counterexample found within this budget”; CutoverProof never labels that as a proof of safety.

# Video upload copy

## Title

CutoverProof — An Agent That Finds the Ordering That Breaks a PostgreSQL Migration

## Description

A PostgreSQL migration can pass review and still corrupt data during the compatibility window. CutoverProof is an adversarial temporal-safety lab for backend and data-platform engineers: Gemini proposes bounded operation schedules, a guarded harness executes them against a freshly reset PostgreSQL database, and independent SQL invariants decide the verdict.

When a counterexample is verified, the product blocks cutover, exposes the exact ordering and violating rows, requires named human approval for an allow-listed repair, and replays the identical schedule. Reasoning proposes; deterministic code decides.

Measured under the same four-candidate budget and model:

- Specialised iterative agent: 3/3 unsafe cases, 0/2 safe false alarms, effort 1.00
- One-shot same-model baseline: 2/3, 0/2, effort 2.33
- Seeded heuristic explorer: 3/3, 0/2, effort 3.00

CutoverProof does not claim to prove a migration safe. It finds the ordering that proves when it is not.

Repository: `https://github.com/Georgexxe/cutoverproof`

Live demo: `https://cutoverproof-1021060138341.us-central1.run.app`

### Chapters

00:00 The compatibility-window problem
00:20 The backend-engineer workspace
00:36 Uploading one fresh JSON migration pack
00:55 Visible bounded-agent execution
01:20 Verified do-not-cut-over decision
01:41 Exact schedule and violating row
02:01 Portable audit timeline
02:22 Named human repair approval
02:40 Identical-schedule replay
02:59 Failure-to-replay audit record
03:15 Architecture and trust boundary
03:37 Fair baseline comparison
04:04 Evidence-integrity improvements
04:27 Final claim

## Suggested tags

`AI agents`, `PostgreSQL`, `database migration`, `Gemini`, `Vertex AI`, `Cloud Run`, `backend engineering`, `agent evaluation`, `developer tools`

## Thumbnail

Use `submission/video/build/01-01_problem.png`.

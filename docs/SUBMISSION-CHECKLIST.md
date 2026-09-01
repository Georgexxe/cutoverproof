# Submission and Scoring Checklist

> Final engineering audit completed 2026-09-01. The public repository and Cloud Run product are live and the 4:24 film is ready. The deadline passed before the platform upload completed, so the remaining external actions are the YouTube upload and a discretionary late-review email. The concise handoff is [`../submission/SUBMISSION-CHECKLIST.md`](../submission/SUBMISSION-CHECKLIST.md).

## Qualification gate: must pass before scoring

### Eligibility and integrity

- [x] Individual submission only.
- [ ] Builder is eligible and registration information is accurate.
- [x] Pre-existing and competition-created work are clearly distinguished.
- [x] All dependencies and reused components comply with licences and terms.
- [x] Synthetic/public data only.
- [x] No credentials, PII, private repositories, or private traces.
- [x] Claims are linked to checked-in evidence.

### Completeness

- [x] Complete solution code.
- [x] Versioned agent instructions/prompts.
- [x] Improvement changelog with real iterations and evidence links.
- [x] Clean-environment reproduction guide.
- [x] Exact advanced, baseline, and evaluation commands.
- [x] Expected output, runtime, model, and cost limitation.
- [x] Solution video at or under five minutes.
- [x] Representative trajectories for every agent used.
- [x] One removed experiment and what it taught.
- [x] Main failure mode and hot take.

### Reproducibility

- [x] Public GitHub repository published from committed `main`.
- [x] Database container starts without local state.
- [x] All versions pinned or constrained.
- [x] U1 and S1 repeat with stable outcomes three times using the same seed.
- [x] Aggregate results regenerate from raw artifacts.
- [x] Timeline regenerates from raw trace.
- [x] Required environment variables are documented without values.

## Rubric readiness

| Criterion | Max | Evidence required before claiming readiness |
|---|---:|---|
| Problem and user value | 15 | Clear backend/data-platform user, temporal bottleneck, concrete payment/status consequence, current workflow and limitation. |
| Agent solution and engineering | 30 | Enforced agent/deterministic boundary, controlled tools, budget, feedback loop, fair ablation, trajectories, failure handling. |
| End-to-end quality | 20 | Scenario input to verified timeline to approved repair replay; artifact a migration engineer can inspect. |
| Measured improvement | 15 | Same-model one-shot and non-agent baseline, equal execution budget, safe controls, raw metrics, honest changelog. |
| Reproducibility | 15 | Clean setup, exact commands, stable seeded results, all assets and prompts included. |
| Hot take/insights | 5 | Demonstrated statement: “Migration tools verify steps. Failures live in schedules.” |

## Five-minute video storyboard

| Time | Content |
|---|---|
| 0:00–0:35 | Intended user, migration bottleneck, and sharp hot take. |
| 0:35–1:05 | Show the simple baseline and its limitation. |
| 1:05–1:40 | Show U1 plan graph and invariant without revealing the answer in advance. |
| 1:40–2:35 | Run specialised agent; show candidate selection and deterministic tool feedback. |
| 2:35–3:15 | Reveal failed SQL assertion and visual timeline with offending row. |
| 3:15–3:50 | Show constrained repair, human approval, and identical schedule replay passing. |
| 3:50–4:25 | Show fair benchmark, safe controls, and raw artifact paths. |
| 4:25–4:50 | Show improvement changelog, most important change, and removed experiment. |
| 4:50–5:00 | Reproduction command and final insight. |

Do not spend video time on login pages, dependency installation, generic architecture narration, or scrolling source code.

## Final claim check

- [x] Every numeric claim appears in generated evaluation output.
- [x] Every shown timeline can be traced to a raw run ID.
- [x] “No counterexample within budget” is not called “safe.”
- [x] Negative or inconclusive results are visible, not deleted.
- [x] Prior-art claims use cautious language from [`PRIOR-ART.md`](PRIOR-ART.md).
- [x] The demo uses no manual database mutation hidden from the audience.

## Upload safety margin

- [x] Stop feature development before submission production begins.
- [x] Produce and test the final archive.
- [ ] Upload the film to YouTube and replace the remaining video-link placeholder.
- [x] Reopen the public repository and live product as an external reviewer.
- [ ] Send the prepared discretionary late-review request.

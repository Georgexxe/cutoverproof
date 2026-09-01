# Competition Brief: micro1 Frontier Engineering Challenge 2026

This is the concise implementation-facing summary. It exists so the coding agent does not need to reread the large source PDFs before beginning.

## Schedule and format

- Competition: micro1 Frontier Engineering Challenge 2026.
- Format: online and individual.
- Kickoff/problem release: 2026-08-28 at 15:00 UTC.
- Submission deadline: **2026-08-31 at 18:00 UTC**.
- Coding-agent use is required.
- Tools must be disclosed and representative agent trajectories submitted.
- Every valid entry must present a simple baseline and an advanced solution with meaningful measured improvement rather than cosmetic variation.

## Qualification gate

A submission is scored only after passing:

- Eligibility.
- Completeness.
- Integrity.
- Trace/trajectory requirements.
- Reproducibility.

A project that cannot be run or verified may be disqualified before rubric scoring.

## Official scoring

| Criterion | Weight | What judges assess |
|---|---:|---|
| Problem and user value | 15 | Meaningful problem, clearly defined user, bottleneck, and why it matters. |
| Agent solution and engineering | 30 | Purposeful, technically sound agent design and engineering choices. |
| End-to-end quality | 20 | Realistic self-contained execution producing a usable result. |
| Measured improvement | 15 | Gains over a fair baseline, with changelog decisions connected to evidence. |
| Reproducibility | 15 | Clean path to run the advanced solution, baseline, and main result. |
| Hot take/insights | 5 | Practical lesson derived from an observed agent failure mode. |

Tie-break order:

1. Agent solution and engineering.
2. Reproducibility.
3. Measured improvement.
4. End-to-end quality.
5. Final evidence review.

## Mandatory submission package

### 1. Complete solution code and improvement changelog

- Include everything needed to run the project, including agent instructions.
- README identifies intended user, bottleneck, and value.
- Every meaningful iteration gets a changelog entry tied to evidence.
- Close with the main failure mode and hot take.

### 2. Reproduction guide

- Written for a clean environment.
- Exact setup, advanced, baseline, and evaluation commands.
- Required data and expected output.
- Relevant versions, approximate runtime, and cost.

### 3. Solution video

- Maximum five minutes.
- Begin with problem and simple baseline.
- Show one realistic end-to-end execution.
- Show final comparison and changelog.
- Highlight the most important change and one removed experiment.

### 4. Agent trajectories

- Representative trajectories for every agent used.
- Instructions, tool calls, tool responses, feedback, retries, and human checkpoints should be followable.

## Rule book

1. Familiar tools/components are allowed.
2. Clearly disclose what existed before the competition and what was added.
3. Follow licences and service terms.
4. Sandbox consequential actions and require human approval before action.
5. Include qualified human review where a solution could significantly affect someone.
6. Use a legal and ethical use case with responsible data handling.
7. Use public, synthetic, or approved anonymous data.
8. Keep credentials/private information outside the submission.
9. Connect every results claim to submitted evidence.
10. Give judges enough access to reproduce the main result.

## Additional submission consideration

The official participation materials state that submissions are governed by the accepted participation agreement and that micro1 may own/use submitted work for model training and evaluation. The participant should confirm the controlling terms before submitting anything they do not intend to grant under those terms.

## CutoverProof alignment

- Synthetic PostgreSQL data only.
- Disposable sandbox only.
- Human approval before repair application.
- Agent trajectories captured by design.
- Baseline and advanced approaches share one verifier.
- Improvement claims are generated from raw runs.
- Reproduction is treated as a release gate, not final-hour documentation.


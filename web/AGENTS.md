# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

## CutoverProof design decisions

- The selected visual target is the light migration mission-control screen supplied on 2026-08-31.
- Use Newsreader for display headings and Alegreya Sans for interface and body text.
- The customer-facing portal is the primary surface. Dense SQL and trace output belong behind “Inspect technical evidence”.
- Never imply that “no counterexample within budget” proves a migration safe.
- The executable boundary is checked-in structured scenarios, declared operations, SQL invariants, and allow-listed sandbox repairs. Do not fake arbitrary-repository execution.
- The signed-in landing screen is a workspace dashboard, never a preselected historical result.
- Workspace, sandbox, account, navigation, new-assessment, import, run, evidence, and sign-out controls must perform their named action.
- Judge-supplied inputs use a validated structured assessment pack and the disposable PostgreSQL sandbox; credentials remain server-memory-only and never enter artifacts.
- “Run guided demo” is the prepared status-normalization PostgreSQL walkthrough: a judge should understand the failure, run it with one click, review the counterexample, approve the bounded repair, and inspect the passing replay.
- “New assessment” is a separate engineer-owned workflow for importing a validated JSON migration assessment pack. Do not mix the prepared demo selector into this flow.
- The product mark is the generated CutoverProof migration-path logo at `src/assets/cutoverproof-mark.png`; use it consistently in authentication, navigation, and browser-brand surfaces.
- The authenticated product is an engineer workspace, never a judge workspace. Do not expose hackathon, submission, reviewer, or “prepared judge experience” language in customer-facing UI.
- The workspace home has exactly two primary entry actions—Run demo and New assessment—followed by recent runs. Connection configuration, execution-service readiness, and benchmark controls are not first-screen tasks.
- Run demo is a coach-mark tour of the real interface that ends by launching the prepared PostgreSQL sample. It must support back, next, skip/exit, and visible focus.
- Safe-control fixtures exist for evaluation but must not appear in the customer assessment library or run history.
- Keep the CutoverProof name. The CP mark leads the brand lockup at a larger size; the text wordmark stays visually quieter so it does not overpower the mark.
- Support the complete customer journey from 320 px phone width upward. Below 420 px, keep the CP mark but hide the visual wordmark text while preserving its accessible label; do not reintroduce document-level minimum widths.

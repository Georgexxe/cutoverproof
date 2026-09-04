# CutoverProof product-readiness status — 2026-09-04

This is the honest status of the nine external-review risks after the product-polish pass.

| Risk | Status | Evidence / remaining work |
|---|---|---|
| Final demo does not prove WebMCP | Product proof complete; recording open | All five tools were called successfully against revision `cutoverproof-00010-xf9`. A continuous recording still must show those calls, the visible draft, human approval, and the resulting run. |
| Demo looks like a slideshow | Open | The application is ready for a click-led recording; the recording itself has not been remade. |
| Workspace may look like fake general AI | Resolved in product | The interface now describes a bounded review workflow and shows deterministic tool activity. It does not claim to be an open-ended model planner. |
| WebMCP feels bolted on | Resolved in product | Live tool discovery, contract inspection, review creation, evidence reading, and repair-review navigation were verified as one workflow. The agent cannot execute or approve. |
| Impact is theoretical | Open | Engineering quality is visible, but credible external-user reactions or adoption evidence remain necessary. |
| Testing access can fail | Resolved and monitored | Secret-backed judge login passed on the final revision. The service is public, warm (`min-instances=1`), and health/model readiness returned OK. |
| State is ephemeral | Mitigated for the bounded demo | The service is pinned to one warm instance with concurrency one, so a job cannot be separated from its session by scale-out. A platform restart can still clear runtime state; durable multi-tenant storage remains outside the demonstrated product boundary. |
| Avoidable frontend debt | Resolved for cited issue | The duplicate legacy App/AppV2 implementation and unused legacy screens were removed. The production build and TypeScript check pass. |
| Modal accessibility | Resolved | Dialogs now have labels, initial focus, focus trapping, Escape handling, scroll locking, and focus restoration. |

## Release gates

1. Record the continuous click-led WebMCP demo.
2. Add real external-user evidence if the submission can still be updated.
3. Keep instance-local state disclosed as a bounded-demo limitation.

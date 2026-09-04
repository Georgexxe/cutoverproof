# CutoverProof product-readiness status — 2026-09-04

This is the honest status of the nine external-review risks after the product-polish pass.

| Risk | Status | Evidence / remaining work |
|---|---|---|
| Final demo does not prove WebMCP | Open | The product now exposes a visible review draft and human handoff, but the final continuous recording still must show tool discovery, real tool calls, the draft, human approval, and the resulting run. |
| Demo looks like a slideshow | Open | The application is ready for a click-led recording; the recording itself has not been remade. |
| Workspace may look like fake general AI | Resolved in product | The interface now describes a bounded review workflow and shows deterministic tool activity. It does not claim to be an open-ended model planner. |
| WebMCP feels bolted on | Substantially improved | A review prepared through WebMCP appears in the live workspace and cannot execute until a human chooses Review & run. The video must still demonstrate this end to end. |
| Impact is theoretical | Open | Engineering quality is visible, but credible external-user reactions or adoption evidence remain necessary. |
| Testing access can fail | Operational gate | Authentication remains. Judge credentials, free availability, and uptime must be confirmed immediately before judging. |
| State is ephemeral | Open | Runtime state remains instance-local. The container now starts from clean evaluation fixtures, but durable shared persistence is not implemented. |
| Avoidable frontend debt | Resolved for cited issue | The duplicate legacy App/AppV2 implementation and unused legacy screens were removed. The production build and TypeScript check pass. |
| Modal accessibility | Resolved | Dialogs now have labels, initial focus, focus trapping, Escape handling, scroll locking, and focus restoration. |

## Release gates

1. Record the continuous click-led WebMCP demo.
2. Confirm judge credentials and deployed uptime.
3. Add real external-user evidence if the submission can still be updated.
4. Treat instance-local state as a disclosed demo limitation unless durable storage is implemented.

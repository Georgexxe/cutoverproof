# ADR-0002: Use structured checked-in scenarios instead of arbitrary repository ingestion

## Status

Accepted

## Context

A production version might ingest migration SQL, application repositories, triggers, job definitions, and natural-language invariants. Implementing reliable extraction for arbitrary projects would exceed the remaining hackathon time and make clean reproduction fragile.

## Decision

Represent the hackathon scenarios through checked-in structured configuration, SQL assets, and named operations. The phase/operation graph is deterministic and scenario-specific. The evaluator's unsafe/safe labels and known schedules remain hidden from the agent-facing view.

## Consequences

### Positive

- Feasible within the deadline.
- Transparent, reproducible, and auditable.
- Keeps attention on temporal experiment selection.
- Makes fair baseline comparison possible.

### Negative

- Users must model their migration rather than point at an arbitrary repository.
- The hackathon artifact is a proof of mechanism rather than a deployable product.
- Generalisation claims must remain modest.

### Neutral

- Agent-assisted scenario extraction can be described only as future work unless actually implemented and evaluated.

## Alternatives considered

### General SQL/repository parser

Rejected for scope and correctness risk.

### Natural-language-only migration description

Rejected because it cannot guarantee executable operations or reproducible semantics.

### Hard-code one failing schedule

Rejected because it would not demonstrate agent selection or support honest baselines.

## References

- [`../../00-FROZEN-DECISION.md`](../../00-FROZEN-DECISION.md)
- [`../PRIMARY-SCENARIO.md`](../PRIMARY-SCENARIO.md)


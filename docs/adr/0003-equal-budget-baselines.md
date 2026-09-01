# ADR-0003: Evaluate all approaches through the same harness and equal schedule budget

## Status

Accepted

## Context

The submission must demonstrate measured improvement over a fair baseline. A static linter alone is an inadequate comparison for a temporal testing system, and giving the advanced agent more attempts or richer information would bias results.

## Decision

Compare the specialised iterative agent with:

1. A one-shot use of the same model with identical scenario facts and operation vocabulary.
2. A non-agent heuristic or seeded-random schedule explorer.

All approaches use the same validator, database reset, executor, verifier, schedule-length limit, and maximum candidate-execution budget. Differences in model calls, wall-clock time, and cost are reported rather than normalized away.

## Consequences

### Positive

- Directly tests whether feedback-driven semantic selection adds value.
- Prevents straw-man baseline claims.
- Makes negative results informative.

### Negative

- The agent may fail its own kill condition.
- Equal execution budget does not make model cost or wall time equal, so both must be disclosed.
- A five-scenario benchmark supports only limited conclusions.

### Neutral

- Static migration tools may be shown for context but are not the decisive baseline.

## Alternatives considered

### Compare only with static linting

Rejected because static tools do not claim to explore temporal schedules.

### Compare with a weaker model

Rejected because improvement might come from model capability instead of harness design.

### Give the advanced agent unlimited attempts

Rejected because it would reward cost rather than selection quality.

## References

- [`../BENCHMARK.md`](../BENCHMARK.md)
- [`../AGENT-HARNESS-CONTRACT.md`](../AGENT-HARNESS-CONTRACT.md)


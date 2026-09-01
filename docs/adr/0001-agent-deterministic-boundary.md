# ADR-0001: Enforce an agent/deterministic verification boundary

## Status

Accepted

## Context

The competition heavily rewards purposeful agent engineering but also requires correctness, traceability, and reproducibility. Allowing a language model to execute arbitrary database changes or judge its own hypotheses would make the result unsafe and unverifiable. Making every decision deterministic would eliminate the agent-specific contribution.

## Decision

Use the agent only for semantic hypothesis formation, candidate-schedule selection, evidence-linked explanation, and selection of a bounded repair. Use deterministic code for scenario validation, database reset, operation execution, SQL invariant verification, budgets, aggregation, timeline rendering, and repair replay.

The boundary is enforced through narrow structured tools. The agent receives no shell and no arbitrary SQL mutation tool.

## Consequences

### Positive

- Judge-visible agent contribution without surrendering correctness.
- Deterministic evidence independently verifies model hypotheses.
- Reduced prompt-injection and accidental mutation surface.
- Baselines can share the same executor and verifier.

### Negative

- More explicit interface work than a single unconstrained agent.
- The agent cannot improvise operations outside the declared scenario.
- Product generality is deliberately limited.

### Neutral

- Explanations remain probabilistic, but their factual references can be checked against traces.

## Alternatives considered

### Fully autonomous database agent

Rejected because it weakens reproducibility, safety, and evidence integrity and violates the sandbox/human-approval spirit of the rules.

### Fully deterministic schedule explorer

Retained as a baseline, rejected as the advanced architecture unless evaluation shows the agent contributes nothing.

### LLM evaluates invariant outcomes

Rejected because SQL assertions can decide the relevant conditions deterministically.

## References

- [`../AGENT-HARNESS-CONTRACT.md`](../AGENT-HARNESS-CONTRACT.md)
- [`../BENCHMARK.md`](../BENCHMARK.md)


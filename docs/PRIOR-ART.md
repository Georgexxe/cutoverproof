# Prior Art and Positioning

## Positioning rule

Do not claim that CutoverProof is globally unprecedented. State the narrower, defensible observation:

> Existing public systems address important portions of migration safety. CutoverProof demonstrates a specialised agent selecting and replaying cross-phase temporal schedules across legacy writes, backfills, compatibility behavior, and cutover, with deterministic business-invariant verification.

## Closest systems

| System | Relevant capability | Boundary from the hackathon thesis |
|---|---|---|
| [pgroll](https://github.com/xataio/pgroll) | Versioned, reversible PostgreSQL schema migrations and backfills | Provides a safer migration mechanism; CutoverProof tests declared schedules and business invariants. |
| [Reshape](https://github.com/fabianlindfors/reshape) | Zero-downtime PostgreSQL schema migration workflow | Mechanism rather than specialised adversarial schedule selection. |
| [gh-ost](https://github.com/github/gh-ost) | Online MySQL schema migration | DDL migration mechanism for another database; not the claimed cross-version business-invariant workflow. |
| [Jepsen](https://github.com/jepsen-io/jepsen) | Adversarial distributed-system consistency testing | Methodological inspiration; generally tests system consistency models rather than a user's expand-contract rollout plan. |
| [VeriEQL](https://github.com/VeriEQL/VeriEQL) | Bounded SQL equivalence checking with counterexamples | Static query semantics rather than temporal migration-phase interleavings. |
| [Cosette](https://github.com/uwdb/Cosette) | Automated reasoning about SQL equivalence | Static SQL reasoning rather than executable cross-version rollout schedules. |
| [Mediator](https://dl.acm.org/doi/10.1145/3158140) | Reasoning about equivalence of database-backed applications across schema changes | Important academic adjacency; distinguish its formal equivalence setting from this executable, budgeted, feedback-driven migration schedule demonstration. |
| [Google F1 schema change protocol](https://research.google/pubs/online-asynchronous-schema-change-in-f1/) | Safe asynchronous schema evolution under a specific protocol | A protocol for F1 transitions, not arbitrary user rollout-plan experiment selection. |
| [GitHub Scientist](https://github.com/github/scientist) | Shadow comparison of old/new code paths | Runtime comparison library rather than migration schedule generation. |
| [Ballast](https://github.com/davemutisya/ballast) | Workload-aware PostgreSQL migration safety analysis | Load/lock analysis is deliberately out of scope for the hackathon build. |
| [Skolem](https://github.com/NguyenTienDat377/Skolem) | SQL equivalence/counterexample workflow | Supports the decision to avoid a broad “SQL counterexample generator” pitch. |
| [Verified Tool Calls](https://arxiv.org/abs/2608.02645) | Tool-call verification and retry reliability | Adjacent to idempotency; CutoverProof uses retry behavior only as one possible migration-schedule factor. |

## Submission language

Good:

- “We found no public tool in our reviewed set that combined these exact elements.”
- “CutoverProof complements migration mechanisms and static analysis.”
- “The hackathon artifact is a reproducible proof of mechanism.”

Bad:

- “Nobody has ever built this.”
- “All existing migration tools are useless.”
- “CutoverProof formally proves migration safety.”
- “The benchmark establishes production performance.”

## What was intentionally removed

- Broad migration lock analysis because Ballast and established migration tools already address adjacent risks.
- Broad SQL fixture generation because VeriEQL, Cosette, and Skolem already occupy much of that space.
- Generic retry/idempotency middleware because specialised systems and research already exist.

The retained contribution is the coherent temporal workflow, not a bundle of unrelated novelty claims.


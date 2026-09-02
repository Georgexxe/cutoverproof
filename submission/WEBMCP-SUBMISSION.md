# CutoverProof — WebMCP submission

## Title

**CutoverProof: The trust layer for agent-led database changes**

## One line

CutoverProof lets a browser agent prepare a migration safety case while PostgreSQL supplies the verdict and a human keeps authority over every consequential action.

## What it does

An engineer planning an online PostgreSQL migration can ask their browser agent to inspect the declared compatibility contract, identify the risk focus, and prepare a review. The review appears immediately in the CutoverProof workspace, but nothing executes until the engineer opens it and explicitly starts the bounded sandbox assessment.

The internal planner then proposes high-value operation orderings. A guarded executor runs only declared operations in a disposable PostgreSQL database. Read-only SQL invariants—not model prose—decide whether a concrete counterexample exists. If a repair is available, the browser agent may open the review, but only a named human can approve the allow-listed replay.

## Why WebMCP matters

Without WebMCP, a browser agent would have to infer product semantics from buttons, cards, and dense evidence tables. CutoverProof exposes the actual change contract and its authority boundaries as five typed browser tools. This lets the agent participate in a high-stakes workflow without granting it invisible production power.

The distinctive interaction is a shared change contract:

- the **agent** prepares and explains;
- the **PostgreSQL verifier** produces evidence and owns the verdict;
- the **human** starts execution and authorizes repairs.

That combination was difficult to express safely through ordinary browser automation: the agent can now receive structured invariants and exact evidence while the product preserves its visible human controls.

## Technical implementation

The signed-in React page registers five imperative tools through `document.modelContext.registerTool`:

- `list_migration_contracts`
- `inspect_migration_contract`
- `create_change_review_draft`
- `read_verified_migration_evidence`
- `open_human_repair_review`

Each tool has a closed JSON Schema, safety-focused description, and appropriate read-only/untrusted-content annotations. Tool handlers reuse authenticated FastAPI endpoints with Pydantic validation, CSRF protection, idempotent draft creation, and the same PostgreSQL allowlist used by the human product. Registration is tied to the authenticated React lifecycle.

The agent cannot start an assessment, send arbitrary SQL, approve a repair, deploy, or alter a verifier result.

## Impact and ambition

AI coding agents are accelerating how quickly production changes are proposed. The missing layer is credible authorization and evidence. CutoverProof starts with the sharp wedge of expand-and-contract PostgreSQL migrations, where individually valid steps can fail only in a particular compatibility-window ordering.

The larger product direction is a trust control plane for agent-mediated production change: declared contracts, bounded experiments, independent verification, human authority, and portable evidence. The submitted product demonstrates that model concretely rather than claiming support for systems it does not yet execute.

## Existing-project disclosure

The adversarial PostgreSQL harness, deterministic verifier, repair replay, and initial React portal existed before this WebMCP submission. During the WebMCP challenge, the product was meaningfully extended with the five-tool browser surface, agent-prepared review objects, live agent–verifier–human workspace, authenticated tool lifecycle, CSRF/rate-limit/security headers, new regression coverage, and WebMCP-specific documentation.

See `docs/WEBMCP-EXTENSIONS.md` and the dated repository history for the exact delta.

## Links

- Live product: `https://cutoverproof-1021060138341.us-central1.run.app`
- Public repository: `https://github.com/Georgexxe/cutoverproof`
- Demo video: `[PUBLIC_UNLISTED_VIDEO_URL]`


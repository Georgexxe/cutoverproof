# WebMCP extension record

Date implemented: 2026-09-02

CutoverProof existed before this WebMCP submission. The work below is the meaningful WebMCP extension added during the challenge submission period. The repository history is the source of truth for timestamps and code changes.

## Before and after

| Area | Before this extension | WebMCP extension |
|---|---|---|
| Browser-agent surface | No registered tools; the browser exposed an empty tool set | Five imperative top-level tools registered with `document.modelContext.registerTool` |
| Agent interaction | Internal Gemini planner selected bounded schedules during an assessment | A visiting browser agent can inspect contracts, prepare a review draft, read verified evidence, and open a human repair review; an in-app Agent workspace makes the same bounded preparation path directly testable |
| Human handoff | Humans started runs and approved repairs through the portal | Agent-prepared reviews now appear as visible workspace objects that explicitly await human action |
| Product framing | PostgreSQL migration testing | Production change control built around an agent–verifier–human authority contract |
| Browser security | HttpOnly SameSite cookie | CSRF token on every authenticated mutation, login throttling, secure deployment cookies, CSP, anti-framing, origin isolation, and an explicit `tools=(self)` Permissions Policy |
| Verification | Backend and customer-flow tests | WebMCP registration, schema, idempotency, no-execution handoff, CSRF, header, and contract-redaction regressions |

## Registered tools

| Tool | Effect | Authority boundary |
|---|---|---|
| `list_migration_contracts` | Reads product-safe contract summaries | No database execution |
| `inspect_migration_contract` | Reads phases, declared operations, invariants, repairs, and authority rules | Raw SQL, evaluator labels, and known failing schedules remain hidden |
| `create_change_review_draft` | Creates an idempotent review draft visible in the human workspace | Does not start PostgreSQL, execute SQL, approve a repair, or deploy |
| `read_verified_migration_evidence` | Reads the verifier-owned verdict, executed ordering, violating rows, and replay state | Clearly preserves the bounded-search claims limit |
| `open_human_repair_review` | Navigates the visible page to an existing repair review | Cannot approve or execute the repair |

The read tools carry `readOnlyHint: true`. Outputs containing scenario or evidence text carry `untrustedContentHint: true`. Every input uses a closed JSON Schema with narrow identifiers, enums, length limits, and `additionalProperties: false`.

## Shared change contract

The product now makes three authorities visible:

1. **Agent — prepare:** inspect the declared contract, focus the risks, and create a review draft.
2. **Verifier — prove:** reset a disposable PostgreSQL database, execute only declared operations, and evaluate read-only invariants.
3. **Human — authorize:** explicitly start an assessment and approve an allow-listed repair replay by name.

This separation is the product feature. WebMCP does not create an invisible automation bypass around the existing UI; it lets an agent contribute structured preparation and evidence while the user retains the consequential decisions.

## Security properties

- Tools register only after an authenticated session is present and unregister when the signed-in React tree is removed.
- WebMCP handlers call the same authenticated, validated FastAPI routes as the human interface.
- Authenticated mutations require the in-memory session's CSRF token.
- Login failures are rate-limited per client address.
- Ephemeral PostgreSQL credentials are scoped to the current session and never returned to tools.
- Review creation is idempotent and records `execution_started: false`.
- Background exceptions are logged server-side but reduced to a generic product error for clients.
- `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Origin-Agent-Cluster`, HSTS on HTTPS, and `Permissions-Policy: tools=(self)` are emitted centrally.

## Reproduce the browser proof

1. Build and run the React/FastAPI product normally.
2. Sign in with the configured demo account.
3. Open the page in a WebMCP-capable ChatGPT in-app browser or supported Chrome build.
4. Confirm that five tools are discoverable.
5. Call `list_migration_contracts`, then `inspect_migration_contract` with `u1_status_trigger_race`.
6. Call `create_change_review_draft` with an objective, one or more risk-focus enums, and a stable idempotency key.
7. Confirm the review appears in the workspace and says that nothing has executed.
8. Select **Review & run** as the human, inspect the contract, and explicitly start the sandbox assessment.

## Verified on 2026-09-02

- Browser discovery: all five tools appeared with their schemas, annotations, page URL, and origin.
- API handoff: authenticated draft creation succeeded; retrying the same idempotency key returned the same draft; `execution_started` remained `false`.
- Python suite: 42 passed.
- React/WebMCP suite: 8 passed.
- TypeScript: no errors.
- Vite production build: succeeded.
- Hosting worker: 4 passed.

## Honest limits

- This remains a single-account, ephemeral demonstration rather than a multi-tenant production service.
- It accepts structured assessment packs, not arbitrary repositories.
- It tests bounded sequential interleavings, not distributed concurrency.
- “No counterexample found” is never represented as proof that a migration is safe.

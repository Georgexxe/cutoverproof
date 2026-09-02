# CutoverProof external-review handoff

## Reviewer brief

CutoverProof tests PostgreSQL expand-and-contract migrations during the compatibility window. A browser agent can inspect a declared change contract, focus the risks, and prepare a visible review. It cannot start the assessment, execute arbitrary SQL, decide the verdict, or approve a repair. PostgreSQL produces the evidence; a named human authorizes consequential steps.

Please review the product as a WebMCP competition entry, not only as a database tool. The key question is whether WebMCP creates a meaningful human-agent collaboration rather than exposing ordinary API wrappers.

**Current handoff status:** the candidate is locally testable, but the public GitHub and Cloud Run deployment are stale as of 2026-09-02. Do not score the public link until the owner confirms the reviewed commit has been pushed and deployed.

## Locations

- Project root: `C:\Users\SURFACE\Documents\ChatGPT\HACKATHON EVALUATION\CutoverProof`
- Public product: `https://cutoverproof-1021060138341.us-central1.run.app`
- Public repository: `https://github.com/Georgexxe/cutoverproof`
- Submission-readiness audit: `submission/SUBMISSION-READINESS-AUDIT-2026-09-02.md`
- Proposed Devpost copy: `submission/WEBMCP-SUBMISSION.md`
- Judge path: `submission/WEBMCP-JUDGE-GUIDE.md`
- WebMCP extension record: `docs/WEBMCP-EXTENSIONS.md`
- Current video draft: `submission/video/CutoverProof_WebMCP_Demo.mp4`
- Video script: `submission/WEBMCP-DEMO-SCRIPT.md`
- Private access note: `submission/private/EXTERNAL-REVIEW-ACCESS.md` — keep this outside the public repository.
- Firecrawl competition archive: `C:\Users\SURFACE\Documents\ChatGPT\HACKATHON EVALUATION\.firecrawl\webmcp-external-review-2026-09-02`

## Core implementation files

| Concern | File |
| --- | --- |
| Browser tool definitions and registration | `web/src/webmcp.ts` |
| Product workspace and direct preparation flow | `web/src/App.tsx` |
| Authenticated API and CSRF client | `web/src/lib/api.ts` |
| WebMCP routes, sessions, security headers, jobs | `src/api/app.py` |
| Closed request contracts | `src/api/schemas.py` |
| Redacted migration-contract projection | `src/api/service.py` |
| Browser-tool unit tests | `web/src/webmcp.test.ts` |
| Product interaction tests | `web/src/App.test.tsx` |
| API, auth, idempotency, and no-execution tests | `tests/test_web_api.py` |
| Architecture and trust boundaries | `docs/ARCHITECTURE.md` |
| Dated pre-existing versus WebMCP delta | `docs/WEBMCP-EXTENSIONS.md` |

## 20-minute review protocol

### Flow A — direct product interaction

1. Open the final deployment and sign in with the privately supplied reviewer credentials.
2. Note whether the first signed-in screen makes the agent, database-verifier, and human roles clear without reading documentation.
3. In the direct preparation workspace, enter: “Inspect the status-normalization contract and prepare a review focused on stale writes during the compatibility window.”
4. Verify that contract discovery, inspection, and review creation appear as live activity.
5. Confirm the created card says that execution has **not** started.
6. Select **Review & run**, inspect the contract, and explicitly start the assessment.
7. Confirm the product returns `DO NOT CUT OVER`, shows the executed schedule, and identifies the violating database row.
8. Open the bounded repair review. Verify that a reviewer name is required.
9. Approve the allow-listed repair and confirm the identical failing schedule passes on replay.

### Flow B — real WebMCP browser agent

Use a WebMCP-capable ChatGPT in-app browser or supported Chrome build.

1. Ask: “List the migration contracts available on this page.”
2. Ask: “Inspect `u1_status_trigger_race` and explain which decisions belong to the agent, PostgreSQL verifier, and human.”
3. Ask: “Prepare a review focused on `stale_writes` and `compatibility_window`.”
4. Confirm the new review becomes visible in the product and nothing executes.
5. After the human runs the assessment, ask the agent to read its verified evidence.
6. Ask the agent to open the repair review. Confirm it can navigate to the decision but cannot approve it.

### Flow C — adversarial checks

1. Enter an ambiguous direct prompt that does not name a contract. Does the app ask for clarification or silently choose one?
2. Try to ask the browser agent to run SQL, start an assessment, or approve a repair. It should explain that no such tool exists.
3. Refresh after preparing a draft. Does state survive as expected?
4. Log out. Confirm the WebMCP tools unregister and protected API calls fail.
5. Reopen the app in a narrow/mobile viewport and check that primary actions remain reachable.

## Scorecard

Score each from 1 (weak) to 5 (exceptional), then give one sentence of evidence.

| Criterion | Score | Evidence |
| --- | ---: | --- |
| WebMCP Leverage: working, non-trivial, appropriate tool surface | /5 | |
| Execution: coherent, reliable end-to-end product | /5 | |
| Potential Impact: credible problem, audience, and demonstrated value | /5 | |
| Creativity & Ambition: different from existing concepts | /5 | |
| Trust clarity: agent/verifier/human authority is unmistakable | /5 | |
| Demo clarity: a judge understands the value in under three minutes | /5 | |

## Questions the owner needs answered

1. In one sentence, what did WebMCP enable that normal UI automation did not?
2. Did any part feel simulated, misleading, or more capable than it really is?
3. Did the direct preparation workspace behave like you expected from its wording?
4. Was the review draft valuable enough to justify an agent interaction, or did it feel like a form fill?
5. Could you explain why this is not just CI migration testing after one run?
6. At what exact moment did you trust—or stop trusting—the product?
7. What would prevent your team from trying this on a real migration?
8. What is the single change most likely to increase its competition score?

## Feedback format

Return:

- reviewer role/background;
- environment and browser used;
- pass/fail for Flows A and B;
- completed scorecard;
- top three blockers in priority order;
- one sentence you would use to describe CutoverProof to another engineer;
- whether the owner may quote your feedback in the submission.

Do not review the current video as final. It predates the latest direct product flow and must be replaced after the public build passes this protocol.

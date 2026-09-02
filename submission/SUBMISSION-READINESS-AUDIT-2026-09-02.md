# CutoverProof WebMCP submission-readiness audit

**Audit date:** 2026-09-02  
**Competition deadline:** 2026-09-03 at 1:00 PM PDT / 8:00 PM UTC / 9:00 PM WAT  
**Verdict:** **NO-GO for final submission until the final demo and judge-path test are complete. The critical public release gap is closed.**

This is an intentionally adversarial review. It separates the product that exists locally from the product a judge can verify on the public internet.

## Executive verdict

CutoverProof has a genuinely distinctive product thesis: an agent prepares a database-change case, PostgreSQL independently proves or disproves it, and a named human retains authority over execution and repair. The deterministic counterexample and identical-schedule repair replay are materially stronger than a generic chat wrapper.

It is not currently the best version this project can be, and it is not yet safe to submit. The WebMCP source is now public and Cloud Run revision `cutoverproof-00008-4sk` is serving the release at 100% traffic. The existing WebMCP video still does not demonstrate the current click-by-click product flow, and the complete browser-agent → human → PostgreSQL → repair journey has not yet been repeated on the final deployment.

If the release, demo, and reviewer-proof gaps are closed, this becomes a credible top-ten contender. It is not an obvious winner yet because the impact case is asserted rather than externally evidenced, and the new in-app “Agent workspace” behaves as a bounded deterministic request router rather than a model-driven assistant. That implementation must be described precisely or improved before judges test free-form prompts.

## Public reality versus local candidate

| Surface | Publicly verifiable now | Local candidate | Consequence |
| --- | --- | --- | --- |
| GitHub | WebMCP source and dated extension history are public through source release `60021ad` | Matches deployed source | Pass |
| Live app | Revision `cutoverproof-00008-4sk` serves 100% traffic | Same frontend and API build | Pass |
| Live API | Public OpenAPI contains the contract and review-draft WebMCP routes | Authenticated smoke test passed | Pass |
| Video | 2:29 WebMCP video exists locally | Current product flow changed after it was rendered | Video is not final and should not be uploaded yet |
| License | MIT is visible in GitHub About | MIT locally | Pass |
| Tests | Public README says 38 Python tests | Current audit: 42 Python, 8 React, 4 Sites; TypeScript clean; production build succeeds | README and public evidence must be refreshed |

## Rubric assessment

Scores below are an auditor estimate, not a prediction of official judging.

| Criterion | Public state now | Local candidate | Honest assessment |
| --- | ---: | ---: | --- |
| WebMCP Leverage | 4.0/5 | 4.0/5 | Five narrow typed tools, closed schemas, authenticated lifecycle, visible human handoff, and bounded authority are substantive. The main write action creates a draft rather than accomplishing the high-value assessment itself, so the leverage is safe but conservative. |
| Execution | 3.8/5 | 4.1/5 | The underlying product, verifier, evidence, repair approval, responsive UI, and tests are coherent. The public release is aligned, but a non-final video and incomplete final judge-path run keep the submission experience unfinished. |
| Potential Impact | 3.0/5 | 3.5/5 | Online migration risk is real and the audience is specific. The submission currently has benchmarks and synthetic fixtures, but no external user validation, deployment team quote, or real migration-repository proof. |
| Creativity & Ambition | 3.8/5 | 4.4/5 | “Agent proposes, database proves, human authorizes” is memorable and differentiated. The narrow PostgreSQL wedge supports a credible trust-control-plane story without pretending to solve every production change. |

**The remaining Stage One risk is the demo:** the official rules require a clear sub-three-minute public YouTube video that matches the functioning product.

## Why this could lose

1. **The final demo still fails to prove WebMCP.** The release gap is resolved, but a judge still needs visible tool discovery, real calls, the live review card, and the human handoff in one continuous recording.
2. **The demo looks like a slideshow.** A polished voice-over cannot replace visible prompts, tool discovery, tool calls, human clicks, and the resulting state transition.
3. **The in-app workspace is mistaken for a fake AI demo.** It uses deterministic keyword routing to call real bounded APIs. It is useful, but it is not a general model planner. Free-form prompts outside its expected vocabulary may silently default to the primary contract and risk focus.
4. **WebMCP feels bolted on.** If the video shows only list/inspect wrappers, judges may decide the browser agent adds convenience rather than enabling a new collaboration. The draft appearing in the live workspace, the execution boundary, evidence reading, and repair-review navigation must be demonstrated as one continuous human-agent workflow.
5. **Impact remains theoretical.** Synthetic scenarios establish technical validity, not adoption. Without even two credible external engineer reactions, the “real problem for a real audience” claim is less persuasive than the engineering quality.
6. **Testing access fails.** The app is authenticated. Missing, expired, or mistyped private Devpost credentials can prevent all judging. The service must remain available free of charge through the judging period.
7. **Ephemeral state surprises a reviewer.** Sessions, drafts, jobs, imported packs, and the Cloud Run sandbox are instance-local. A restart or scale-out can erase state or separate a session from its job unless the deployment is pinned to a single instance. This is acceptable for a bounded demo only if the judge path is stable and rehearsed.
8. **Code reviewers see avoidable debt.** `web/src/App.tsx` contains both the unused legacy `App` and active `AppV2` in one large file. It builds, but it weakens the impression of a finished product.
9. **Accessibility review catches modal behavior.** Dialogs support Escape and labels, but lack a complete focus trap, initial focus placement, and focus restoration. This is not a hackathon blocker, but it is a real product-quality gap.

## Go/no-go gates

Do not submit until every P0 gate is green.

### P0 — submission blockers

- [x] Push the WebMCP source and dated extension history to public `main`.
- [x] Deploy source release `60021ad` to the existing Cloud Run service.
- [x] Confirm the public OpenAPI contains `/api/webmcp/contracts` and `/api/webmcp/review-drafts`.
- [ ] Sign in using the exact credentials that will be placed in Devpost and complete both the in-app and browser-agent paths.
- [ ] Verify all five WebMCP tools register in a supported judge environment.
- [ ] Record a new sub-three-minute demo from the final public build with real prompts, visible tool activity, user clicks, evidence, and human approval.
- [ ] Upload the video to public/unlisted YouTube and replace `[PUBLIC_UNLISTED_VIDEO_URL]`.
- [ ] Confirm the Devpost draft contains the live URL, public repo, testing credentials, English description, and final video.

### P1 — score improvements worth doing before final capture

- [ ] Make the in-app direct interaction unambiguous: either upgrade it to a real model-planned assistant or explicitly label it as a bounded preparation console. Never claim the deterministic router is a general AI agent.
- [ ] Handle ambiguous prompts by asking the user to choose a contract instead of silently defaulting.
- [ ] Remove the unused legacy React `App`, or at minimum split the active product into reviewable components.
- [ ] Run two external 15-minute tests and capture specific feedback or quotations, with permission, about the problem and authority boundary.
- [ ] Add one end-to-end regression that verifies login → draft creation → no execution → human start → evidence → human repair approval.
- [ ] Correct README test counts and make the WebMCP extension the first thing a judge sees.

### P2 — post-submission product work

- Persistent database-backed sessions, drafts, jobs, and imported packs.
- Self-service organizations, users, projects, roles, audit retention, and real SSO.
- Migration-repository ingestion and contract generation rather than JSON-only packs.
- Parallel/distributed interleaving simulation and more verification boundaries.
- Complete dialog focus management and broader accessibility testing.

## Official competition facts

- Competition: [WebMCP Challenge](https://webmcp.devpost.com/)
- Official rules: [Rules](https://webmcp.devpost.com/rules)
- Deadline: **September 3, 2026 at 1:00 PM PDT (8:00 PM UTC / 9:00 PM WAT)**
- Judging: September 4, 2026 at 10:00 AM PDT through September 21, 2026 at 5:00 PM PDT
- Winner announcement target: September 23, 2026 at 2:00 PM PDT
- Ten winning submissions are listed; each includes a $3,000 OpenAI cash prize plus sponsor prizes described in the official rules.
- The four Stage Two criteria are equally weighted: WebMCP Leverage, Execution, Potential Impact, and Creativity & Ambition.
- Existing products are judged only on the work added during the submission period and require clear dated evidence of the WebMCP extension.
- Required materials include a working live URL, an English description of WebMCP fit and human-agent collaboration, a public repository with detectable open-source license, and a clear public YouTube demo under three minutes.

## Reproducible evidence used for this audit

- Firecrawl archive: `../.firecrawl/webmcp-external-review-2026-09-02/`
- Official pages captured: `official-main.md`, `official-rules.md`, `official-dates.md`, `chrome-webmcp.md`
- Public-state captures: `public-repo.md`, `live-app.md`, `live-health.md`, `live-openapi.md`
- Fresh visual capture: `output/audit-2026-09-02/01-login.png`
- Local verification on 2026-09-02: 42 Python tests passed, 8 React tests passed, 4 Sites packaging tests passed, TypeScript passed, and the Vite production build completed with 362 transformed modules.

## Final recommendation

The public links now represent the WebMCP candidate and can be sent to external reviewers with `submission/EXTERNAL-REVIEW-HANDOFF.md`. Treat the existing WebMCP video as a draft. The remaining proof chain must be completed honestly: **public commit → deployed build → real tool call → visible human handoff → database evidence → final video.**

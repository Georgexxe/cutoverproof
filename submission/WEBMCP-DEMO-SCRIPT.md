# WebMCP demo — continuous click-led recording

Target runtime: 2:10–2:30. Record one continuous browser session with the pointer visible. Do not rebuild the old slideshow render. The product, prompts, tool calls, human clicks, and state changes must all be visible.

## 0:00–0:15 — Set up the risk

**Screen:** Begin on the signed-in Home screen.

**Voice:** “A PostgreSQL migration can pass review and still corrupt data during rollout. The failure is often an ordering: backfill, an old writer, and cutover are each valid alone, but unsafe together.”

## 0:15–0:43 — Discover and inspect real tools

**Clicks and prompts:** Open the browser's available-tools surface so the five CutoverProof tools are visible. Ask: “List the migration contracts on this page.” Then: “Inspect `u1_status_trigger_race`. Who controls preparation, verification, and approval?” Keep the returned tool calls on screen.

**Voice:** “WebMCP gives the browser agent a typed change contract. It can inspect phases, declared operations, invariants, and allowed repairs. It receives no arbitrary SQL tool and no authority to execute or approve.”

## 0:43–1:02 — Create the visible handoff

**Prompt:** “Prepare a review for `u1_status_trigger_race`, focused on stale writes and the compatibility window.”

**Screen:** Show the review card appear on Home. Point to **Not run yet**, then click **Review & run**.

**Voice:** “The only write creates a review—not an execution. The draft appears in the same workspace, and nothing runs until I inspect it and choose Run assessment.”

## 1:02–1:32 — PostgreSQL supplies the verdict

**Clicks:** Click **Run assessment**. Keep the live Validate, Plan, Execute, Verify, and Evidence stages visible. When complete, click **View evidence**.

**Voice:** “Gemini proposes a dangerous schedule, but PostgreSQL executes it and a read-only invariant decides the result. One old write leaves the new status reference stale, so CutoverProof blocks cutover and shows the exact ordering and row.”

## 1:32–2:03 — The agent stops at the human boundary

**Prompts:** “Read the verified evidence for this run.” Then: “Open the human repair review.”

**Clicks:** Show the repair dialog, type the reviewer name yourself, and click **Approve & replay**. Do not let narration or edits hide these clicks.

**Voice:** “The agent can read the database evidence and open this decision. It cannot approve. I authorize one allow-listed repair, and CutoverProof replays the identical failing schedule.”

## 2:03–2:20 — Close on proof, not promise

**Screen:** Hold on **REPAIR VERIFIED IN SANDBOX**.

**Voice:** “The same schedule now returns zero violating rows. CutoverProof does not claim every schedule is safe. It proves this failure, records the human decision, and verifies this bounded repair.”

## Recording gates

- One continuous browser capture; no slide sequence.
- Pointer, typed prompts, tool names, tool responses, human clicks, and state transitions remain visible.
- Show all five tool names and visibly exercise all five.
- Never expose the judge password or any token.
- Final frame includes the live-product and repository links.
- Do not submit `submission/video/CutoverProof_WebMCP_Demo.mp4`; it predates this live workflow.

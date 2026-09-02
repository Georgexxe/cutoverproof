# WebMCP judge guide

## Fastest path

1. Open the live product in the ChatGPT in-app browser or a supported WebMCP Chrome build.
2. Sign in using the credentials supplied privately in the Devpost testing instructions.
3. Confirm the workspace shows **5 browser tools ready**.
4. Ask the agent to list the migration contracts.
5. Ask it to inspect `u1_status_trigger_race` and explain the agent, verifier, and human authority boundaries.
6. Ask it to create a review draft focused on `stale_writes` and `compatibility_window`.
7. Confirm the draft appears in the visible workspace and explicitly says that nothing has executed.
8. Select **Review & run**, inspect the contract, and start the bounded assessment as the human.
9. Read the `DO NOT CUT OVER` result and exact violating row.
10. Ask the agent to read the verified evidence or open the repair review. Confirm that it still cannot approve the repair.
11. Enter a reviewer name and approve the allow-listed repair in the UI. Confirm the identical-schedule replay passes.

## Expected boundary

The agent can prepare a review, read deterministic evidence, and navigate to a consequential decision. It cannot execute arbitrary SQL, start production work, decide pass/fail, or approve a repair.

## Fallback

If the model provider is temporarily unavailable, browser-tool discovery, contract inspection, and review-draft creation still work. The repository also contains previously executed, reproducible PostgreSQL evidence under `artifacts/`.


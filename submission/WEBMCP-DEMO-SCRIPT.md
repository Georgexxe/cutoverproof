# WebMCP demo — final runtime 2:30

## 0:00–0:18 — The risk

“AI agents can propose production changes faster than teams can safely review them. The dangerous question is not whether each migration step is valid. It is whether one compatibility-window ordering corrupts the result.”

Show the CutoverProof home and the three authorities.

## 0:18–0:38 — The product thesis

“CutoverProof is a trust layer for agent-led database changes. The agent prepares. PostgreSQL proves. The engineer authorizes.”

Show **5 browser tools ready** and briefly reveal the discovered tool list.

## 0:38–1:03 — Structured agent preparation

Ask the browser agent to list contracts, then inspect `u1_status_trigger_race`.

“WebMCP gives the agent the real phases, operations, invariants, repairs, and authority boundary. It does not scrape those meanings from the interface, and it never receives raw SQL or hidden evaluator answers.”

## 1:03–1:25 — Visible handoff

Ask the agent to create a review focused on stale writes and compatibility-window risk.

Show the review card appear.

“This is the only write tool. It creates an idempotent review draft. Nothing has executed. I still have to review the contract and start the sandbox assessment.”

## 1:25–1:54 — Independent proof

Select **Review & run** and start the assessment. Cut to the completed result and technical evidence.

“The internal planner chooses a dangerous ordering, but PostgreSQL executes it and a read-only invariant supplies the verdict. Here, an old write leaves the new status reference inconsistent, so CutoverProof blocks cutover with the exact row and ordering.”

## 1:54–2:19 — Human authority

Ask the agent to read the verified evidence and open the repair review.

“The agent can explain the evidence and open this decision. It cannot approve it. I enter my name, approve one allow-listed repair, and CutoverProof replays the identical failing schedule.”

Show **REPAIR VERIFIED IN SANDBOX**.

## 2:19–2:30 — Close

“This starts with PostgreSQL migrations, but the product idea is broader: every agent-led production change should have a declared contract, bounded experiments, independent proof, and a human authority line it cannot cross.”

End on the home authority strip and repository/live-product links.

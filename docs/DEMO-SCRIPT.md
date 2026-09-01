# Final demo film

- Rendered file: `submission/video/CutoverProof_Competition_Demo_FINAL.mp4`
- Captions: `submission/video/CutoverProof_Competition_Demo_FINAL.srt`
- Duration: 4 minutes 41.46 seconds
- Delivery: 1920×1080, H.264 video, AAC narration
- Script source: `submission/video/narration.json`
- Rebuild scripts: `scripts/render_submission_voice.ps1` and `scripts/render_submission_video.py`

## Storyboard

| Time | Evidence shown | Competition question answered |
|---|---|---|
| 0:00–0:20 | Compatibility-window problem | Who has the bottleneck and why does it matter? |
| 0:20–0:36 | Fresh engineer workspace | Is this a usable product rather than a chat response? |
| 0:36–0:55 | Fresh JSON pack uploaded from Downloads with its contents visible | What realistic input starts the workflow? |
| 0:55–1:20 | Enlarged live job state: validate, plan, execute, verify, evidence | What does the bounded agent do purposefully? |
| 1:20–1:41 | `DO NOT CUT OVER` decision and exact conflict marker | What useful decision did the engineer receive? |
| 1:41–2:01 | Executed ordering and violating PostgreSQL row | What deterministic evidence supports the verdict? |
| 2:01–2:22 | Readable portable timeline | Can the customer audit and reproduce the result? |
| 2:22–2:40 | Named human approval of the uploaded pack's allow-listed repair | How is a consequential action controlled? |
| 2:40–2:59 | Identical-schedule replay verified | Did the bounded repair pass the same test? |
| 2:59–3:15 | Audit record joining the failure, approval, and replay | Is the full safety case preserved? |
| 3:15–3:37 | Layered architecture and trust boundaries | Where does model reasoning stop and deterministic verification begin? |
| 3:37–4:04 | Equal-budget comparison | What measured improvement exists over fair baselines? |
| 4:04–4:27 | Professional evaluation improvements | How did evaluation strengthen evidence integrity? |
| 4:27–4:41 | Close | What is—and is not—claimed? |

## Claims used in the film

- A3 specialised agent: 3/3 unsafe cases found, 0/2 safe false alarms, mean effort 1.00.
- Same-model one-shot baseline: 2/3 unsafe cases found, 0/2 safe false alarms, mean effort 2.33.
- Seeded heuristic: 3/3 unsafe cases found, 0/2 safe false alarms, mean effort 3.00.
- The agent proposes schedules and hypotheses; SQL invariants supply the verdict.
- Repair is a checked-in allow-listed template, requires named approval, and replays the identical failing schedule.

Do not claim exhaustive safety, production readiness, exact provider cost, or unseen-scenario generalization.

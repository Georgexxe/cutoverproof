# Final submission checklist

## Qualification gate

- [x] Individual project scope and provenance disclosed.
- [x] Public/synthetic data only.
- [x] Consequential repair is sandboxed and human-approved.
- [x] Secrets excluded from repository artifacts.
- [x] Clean local reproduction instructions in `README.md`.
- [x] Solution, baselines, data, model, seed, budget, runtime, and limitations documented.
- [x] Agent/tool trajectories provided for every valid model run.
- [x] Improvement changelog links claims to evidence.
- [x] Demo film is under five minutes.
- [x] Final film contains problem, baseline, realistic start-to-finish execution, measured comparison, changelog, biggest contributor, and one removed experiment.

## Verification

- [x] Python suite: 38 passed.
- [x] React suite: 4 passed.
- [x] TypeScript: no type errors.
- [x] Production frontend build succeeds.
- [x] Built-in example completes against PostgreSQL.
- [x] Three independent JSON imports complete against PostgreSQL.
- [x] Human-approved identical-schedule repair replay passes.
- [x] Desktop responsive QA.
- [x] 390×844 mobile responsive QA with no document overflow.
- [x] Video: 281.46 seconds, 1920×1080 H.264/AAC, 70 non-overlapping caption cues included.
- [x] Cloud Run health and sign-in verified.
- [x] Cloud Run Vertex prediction permission granted and live assessment re-verified.

## External publication

- [x] Public GitHub repository URL added to submission copy.
- [ ] Final MP4 uploaded and public/unlisted URL added.
- [x] Live Cloud Run product linked and end-to-end verified.
- [ ] Late-review request emailed because the competition deadline passed before upload completed.

## Files to submit or link

- `submission/FINAL-SUBMISSION-PACKET.md`
- `submission/JUDGE-GUIDE.md`
- `submission/VIDEO-UPLOAD-COPY.md`
- `submission/video/CutoverProof_Competition_Demo_FINAL.mp4`
- `submission/video/CutoverProof_Competition_Demo_FINAL.srt`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/IMPROVEMENT-CHANGELOG.md`
- `docs/BENCHMARK-RESULTS.md`
- `artifacts/trajectories/`

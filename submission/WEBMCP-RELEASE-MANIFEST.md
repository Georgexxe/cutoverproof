# CutoverProof WebMCP release manifest

Generated and verified on 2026-09-05.

## Submission video

- **Submit this file:** `submission/video/CutoverProof_WebMCP_Submission_FINAL.mp4`
- Runtime: 157.000 seconds (2:37)
- Container: MP4
- Video: H.264, 1920×1080, 24 fps, yuv420p
- Audio: AAC, 48 kHz, mono
- Size: 5,849,413 bytes
- SHA-256: `C8375CE6A78D67CB948114E97B716C794F8E567B67102E0CA7AAD5C5FBBF461F`
- Decode verification: FFmpeg completed a full decode with zero reported errors
- Capture treatment: one continuous product-led story built from current app captures and the successful live run; no title or architecture slides
- Privacy treatment: Codex task chrome, browser chrome, and the recording-control toast are absent; no credentials or private task names appear
- Proof labels: timed overlays name all five WebMCP calls while those calls are exercised in the recorded workflow
- Captions: burned into the video for judge-readable playback without a separate subtitle track
- Narration voice: Google Cloud TTS `en-GB-Chirp3-HD-Charon`, matching the established CutoverProof competition-film voice

## Workflow proven in the take

1. `list_migration_contracts` returns the five bounded contracts without executing a migration.
2. `inspect_migration_contract` returns declared phases, operations, invariant, repair, and authority boundary.
3. `create_change_review_draft` creates a visible, idempotent draft in `awaiting_human_review`; execution remains false.
4. A human starts the PostgreSQL sandbox assessment; the verifier returns `DO NOT CUT OVER` and row 42 (`shipped` versus `pending`).
5. `read_verified_migration_evidence` returns the failing schedule and verifier-owned row evidence.
6. `open_human_repair_review` opens the decision surface but cannot approve.
7. A named reviewer approves the allow-listed sandbox repair and CutoverProof replays the same schedule.
8. The take closes on `REPAIR VERIFIED IN SANDBOX` with replay time visible.

## Verification commands

```powershell
& 'C:\Program Files\FFmpeg\8.1.2\bin\ffprobe.exe' -v error -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels -of json submission\video\CutoverProof_WebMCP_Submission_FINAL.mp4
& 'C:\Program Files\FFmpeg\8.1.2\bin\ffmpeg.exe' -hide_banner -v error -i submission\video\CutoverProof_WebMCP_Submission_FINAL.mp4 -f null NUL
Get-FileHash -Algorithm SHA256 submission\video\CutoverProof_WebMCP_Submission_FINAL.mp4
```

## Reproducible edit sources

- Narration plan: `submission/video/webmcp-live-narration.json`
- Timed labels and burned captions: `submission/video/webmcp-interactive.ass`
- Voice generator: `scripts/render_webmcp_voice.ps1`
- Final render pipeline: `scripts/render_webmcp_interactive.py`
- OBS local-control helper: `scripts/obs-control.mjs`

The earlier `submission/video/CutoverProof_WebMCP_Demo.mp4` is a superseded slideshow-style draft and must not be submitted.

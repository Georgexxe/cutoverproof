# Release manifest

## Product verification

- Python: `38 passed`
- React customer workflow: `4 passed`
- TypeScript: no errors
- Vite production build: succeeded, 361 modules transformed
- Built-in example: executed counterexample in PostgreSQL
- Independent imports: three distinct JSON packs executed
- Repair: named approval plus identical-schedule replay passed
- Responsive QA: laptop and 390×844 mobile, no document-level horizontal overflow

## Final film

- File: `CutoverProof_Competition_Demo_FINAL.mp4`
- Duration: `281.463000` seconds
- Video: H.264, 1920×1080
- Audio: AAC, mono; measured mean −17.7 LUFS, true peak −1.9 dBFS
- Captions: 70 cues, no overlaps, final cue ends at 280.79 seconds
- SHA-256: `47FDAE5D5F769A25A0239B3A6A5EF76B1919F45B464CC22D9A9E7943B73AA167`

## Public release

- Repository: `https://github.com/Georgexxe/cutoverproof`
- Live product: `https://cutoverproof-1021060138341.us-central1.run.app`
- Cloud Build: `fa3aee25-644d-44f8-ada0-adca5a3e6b34` (`SUCCESS`)
- Cloud Run revision: `cutoverproof-00007-mrc` (100% traffic)
- Container digest: `sha256:151a50328c402532cf54e924003b916ef953d698f6f9d929ea41bfb0a07984a6`
- Live workflow: health, login, Vertex assessment, PostgreSQL verdict, approval, and repair replay passed; see `docs/LIVE-DEPLOYMENT-VERIFICATION.md`.

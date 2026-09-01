# Tools and provenance disclosure

## Project provenance

No CutoverProof application code existed before this competition. The idea selection, fixtures, application, tests, benchmark, evidence, customer portal, deployment configuration, and submission assets were produced during the challenge window.

An external coding-agent pass produced the initial repository scaffold from a written implementation handoff. Its exact provider/build identifier was not preserved, so it is disclosed here as an **external coding-agent scaffold** rather than attributed to an unverified model. OpenAI Codex Desktop then audited and substantially revised the product: deterministic failure handling, evidence integrity, repair approval, customer workflow, responsive interface, settings, test coverage, Cloud Run packaging, final benchmark documentation, and submission film.

## AI and agent tools

| Tool | Purpose | Boundary |
|---|---|---|
| OpenAI Codex Desktop | Research synthesis, code audit, implementation changes, tests, browser QA, deployment packaging, documentation, and final film assembly | Human-directed development tool; not part of the runtime migration verdict |
| Gemini `gemini-3.1-flash-lite` | Runtime A1 one-shot and A3 iterative schedule proposals; repair-template selection after verified failure | Receives only the declared operation catalog; cannot execute arbitrary SQL/shell and never determines pass/fail |
| Google Cloud Text-to-Speech | Narration for the final demo film | Presentation only |
| Self-hosted Firecrawl | Competition, prior-art, and problem research capture | Research only; no hosted credits and no runtime dependency |

## Development and delivery tools

- Python 3.12 / FastAPI / Pydantic
- React 18 / TypeScript / Vite
- PostgreSQL 16 for the audited local benchmark; PostgreSQL 17 in the Cloud Run image
- Docker / Docker Compose
- pytest / Vitest / Testing Library
- Google Cloud Run, Artifact Registry, and Vertex AI
- FFmpeg and Pillow for deterministic video assembly
- Git for the final clean repository archive

## Reused components

The project uses the pinned or constrained open-source packages listed in `requirements.txt`, `pyproject.toml`, and `web/package.json`, plus the official PostgreSQL packages in the container. CutoverProof source is released under MIT; dependencies retain their own licences. The selected Newsreader and Alegreya Sans font files are used in the submission film and retain their upstream font licences.

## Evidence integrity

Agent/tool trajectories under `artifacts/trajectories/` are runtime application traces—not transcripts of the coding assistants. Failed provider experiments are retained under `artifacts/invalidated/`. No scenario-aware offline planner remains in production code.


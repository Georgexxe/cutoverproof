# Login design QA

**Source visual truth:** `docs/ux-audit/00-login-source.png`  
**Implementation:** `docs/ux-audit/02-login-fixed-laptop.png`  
**Responsive evidence:** `docs/ux-audit/03-login-fixed-mobile.png`  
**Combined comparison:** `docs/ux-audit/04-login-source-vs-fixed.png`

## Capture details

- Desktop source: 1110 × 675 px.
- Desktop implementation: 1110 × 675 CSS px at 1× density.
- Mobile implementation: 390 × 844 CSS px at 1× density.
- State: signed out, empty credentials, no validation error.
- Route: `http://127.0.0.1:4173/`.

## Findings

No actionable P0, P1, or P2 issues remain.

- Fonts and typography: Newsreader remains the display face and Alegreya Sans remains the interface/body face. The white hero heading now has strong contrast and a controlled desktop wrap.
- Spacing and layout rhythm: desktop uses a balanced split layout with the complete form above the fold; mobile makes sign-in the first screen and keeps all controls inside the viewport.
- Colors and visual tokens: the established navy/indigo palette is preserved; foreground contrast is corrected; focus, border, and CTA tokens remain consistent with the product.
- Image quality and asset fidelity: the supplied CutoverProof mark is reused at native quality and increased to a legible size. No placeholder or reconstructed logo was introduced.
- Copy and content: the form is customer-facing, uses neutral placeholders, and no longer exposes a fake engineer email.
- Accessibility: semantic labels and autocomplete hints are present, the form region is named, and the core controls remain keyboard reachable.

Focused-region comparison was not required: the logo, hero copy, field labels, inputs, CTA, and helper line are legible in the full-size same-viewport comparison.

## Comparison history

1. Initial P0: hero heading inherited the dark global heading color and became unreadable against navy. Fixed with an explicit high-contrast hero foreground.
2. Initial P1: the 1050 px breakpoint stacked the login panel below the fold on ordinary laptop widths. Fixed by retaining the split view through 880 px.
3. Initial P1: mobile showed marketing before authentication. Fixed by placing the sign-in panel first and adding the existing brand mark to the card.
4. Initial P2: a hard-coded non-login email suggested fake customer state and caused avoidable authentication failure. Fixed with an empty value and neutral placeholder.
5. Post-fix evidence at 1110 × 675 and 390 × 844 shows the complete primary action without horizontal overflow or hidden controls.

## Interaction checks

- Empty email and password fields are visible and required.
- Password remains masked and advertises `current-password` autocomplete.
- The primary submit action is visible at both tested breakpoints.
- Browser DOM contains the named sign-in region and product-safeguards list.

**final result: passed**

---

# Final product and submission-film QA

## Evidence reviewed

- Fresh desktop workspace: `submission/video/frames/33-final-browser-home.png`.
- Fresh JSON import with the uploaded configuration visible: `submission/video/frames/21-fresh-json-imported.png`.
- Real job progression: `submission/video/frames/22-live-progress.png` and enlarged film frame `submission/video/frames/32-live-progress-focus.png`.
- Decision, corrected conflict marker, evidence, approval, and replay: `submission/video/frames/24-imported-decision.png` through `submission/video/frames/29-repaired-detailed-timeline.png`.
- Final settings: `submission/video/frames/34-final-settings.png`.
- Phone workspace and assessment modal at 390 × 844: `submission/video/frames/35-mobile-check.png` and `submission/video/frames/36-mobile-assessment-modal.png`.
- Final film contact sheet and timed live-progress frame: `submission/video/build/final-contact-sheet.png` and `submission/video/build/qa-progress-at-65s.png`.

## Findings

No actionable P0, P1, or P2 product or film issues remain.

- The customer journey is one continuous story: one fresh JSON upload, real execution progress, one database-backed counterexample, readable evidence, named approval, and identical-schedule repair replay.
- The phase rail labels the actual conflict—`Legacy write after backfill`—without overlapping phase nodes.
- The evidence modal and HTML timeline explain the exact ordering and returned row before exposing optional raw SQL.
- The settings page uses customer-facing controls and clearly separates configurable defaults from permanent safety boundaries.
- The mobile layout keeps navigation usable, stacks the three-step overview, and presents the assessment modal without horizontal overflow.
- The architecture visual distinguishes customer, human approval, Cloud Run workflow, external Gemini reasoning, deterministic PostgreSQL execution, SQL verdict authority, and recorded evidence.
- Narration describes only what is visible in its paired frame. The old claim that three additional packs were visibly imported in the film is removed.
- Final delivery is 1920 × 1080 H.264 with AAC narration, 281.463 seconds, and 70 non-overlapping caption cues.

**final result: passed**

---

# Authenticated product design QA

## Tested states

- Desktop: 1440 × 900, signed in, fresh workspace.
- Mobile: 390 × 844, signed in, fresh workspace.
- Navigation: Home, Assessments, and Settings only.
- Assessment history: empty until the signed-in user completes an assessment in the current product session.
- New assessment: initial choice state, built-in example loaded, and visible editable JSON configuration.

## Findings

No actionable P0, P1, or P2 interface issues remain.

- Information architecture: customer-visible Runs was removed because a run is an execution detail of an assessment, not a separate customer object.
- First-use state: seeded benchmark and sample results no longer appear as the engineer's history. Assessments shows a single empty-state CTA until the engineer creates one.
- Import flow: the modal contains only Load example template and Choose JSON file before selection. Loading either source reveals the full editable JSON immediately.
- Demo isolation: the built-in onboarding template remains separate from three validated upload packs kept for video demonstrations.
- Responsive layout: the compact header now keeps Home, Assessments, Settings, and account access on one row; content starts below it without overlap. The assessment modal stacks its source actions and keeps the JSON editor and run action usable at 390 × 844.
- Visual system: Newsreader and Alegreya Sans, the existing CutoverProof mark, spacing, borders, and indigo interaction tokens remain consistent across laptop and phone views.

## Verification

- Browser inspection confirmed the fresh Home and empty Assessments states.
- Browser inspection confirmed the loaded example displays its JSON rather than a collapsed readiness summary.
- TypeScript typecheck passed.
- Production Vite build passed.
- API regression suite validates all three distinct video-demo JSON packs.

**final result: passed**

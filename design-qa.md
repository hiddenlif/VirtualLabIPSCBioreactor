# Interface design verification · v2

Verified 2026-10-26 10:54 PDT.

## Visual evidence

- Source visual truth: [approved reference](reports/design-v2/approved-reference.png), 1487 × 1058 pixels.
- Implementation: [desktop capture](reports/campaign-screen-v2.png), 1487 × 1058 pixels; CSS viewport 1487 × 1058. Browser output normalized to one output pixel per CSS pixel. Full-page spatial capture cropped to the viewport; no content stretching.
- [Full-view comparison](reports/design-v2/comparison.jpg): reference on the left, implementation on the right, equal pixel dimensions.
- [Focused inspector comparison](reports/design-v2/inspector-comparison.jpg): native-size crops for typography, controls, spacing and copy.
- [Phone capture](reports/design-v2/mobile.png): 390 × 844 CSS/output pixels. Also checked at 1024 px desktop width. No horizontal page overflow at 390 px.
- State: EXP-0017 at 48 h; independent pH selected; illustrative motion playing. Actual telemetry and QC hold retained.

## Findings and comparison history

No actionable P0/P1/P2 issues remain in the reviewed views.

1. Initial implementation hid the new-campaign and dossier actions with the old heading. Fixed by moving the actions into the persistent toolbar; export verified through the browser.
2. Phone telemetry overlapped the vessel. Moved the readings below the vessel at narrow widths and captured the repaired 390 px layout. The wide toolbar initially consumed an extra row; compacted it and enlarged the vessel before the final same-viewport comparison.
3. Final desktop and inspector comparisons were inspected together against the approved reference. Published captures show the repaired state.

## Required fidelity surfaces

| Surface | Assessment |
| --- | --- |
| Fonts and typography | Georgia display headings and wordmark, system sans-serif labels, and spaced monospace metadata retain the selected editorial lab character. The generated reference has no authoritative font metadata; these are deliberate local fallbacks. |
| Spacing and layout rhythm | Slim persistent rail, broad scientific canvas, restrained dividers and contextual right inspector retained. Layout stacks on phone widths. Actual evidence, controls and explanatory copy require more vertical space than the concept. |
| Colors and tokens | Shared near-black plum background, soft white, muted violet, chartreuse actions and cyan signal palette. Amber retains its evidence-status meaning. Focus outlines remain visible. |
| Image quality | Generated transparent chrome/glass vessel matches the selected art direction without a rectangular background. The small liquid displacement preserves the vessel silhouette. GIF is 64 frames, eight seconds, 1200 × 854, approximately 1.1 MiB. |
| Copy and content | Retained real assay costs, delays, pending/result distinction, campaign time and QC hold. The concept’s simplified trace is replaced by actual simulator history. Motion is explicitly illustrative. |

## Behavior and verification

- Browser checks: independent branch; request pH assay; pending result; advance from 48 to 54 h; valid returned result; investigation, evidence, study and methods navigation; JSON dossier download; motion pause/play; focus retained on motion toggle; assay selection updates requested panel without replacing the focused input.
- Browser error logs: no errors in final checked previews.
- 16 existing unit tests passed. Retained scientific results verification passed. JavaScript syntax check passed. Ruff 0.17.2 check and format check passed.
- Reduced-motion behavior is implemented through the media query at startup and changes; app pause was browser-tested. An OS preference switch was not exercised. Illustration motion does not mutate simulation state and stops in hidden tabs.

## Accepted differences and remaining limits

This is a faithful application of the approved visual direction to the existing scientific application, not a pixel copy of invented data or decorative controls. Original navigation destinations and scientific workflow remain available. The additional campaign controls and evidence-status strip are intentional. The README GIF is a recorded preview; actual interaction requires running the local app.

P3 follow-up: a dedicated display font could refine the wordmark if the project later accepts a font dependency. Automated screen-reader and OS-level reduced-motion testing were not performed.

## Implementation checklist

- [x] Approved art direction and full-view/focused comparisons
- [x] Desktop and phone captures
- [x] Primary workflows and exports checked in browser
- [x] Scientific regression checks retained
- [x] Original screenshots preserved; new previews versioned

final result: passed

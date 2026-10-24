# Development verification

The dated checks below describe the initial implementation. The later [Ruff maintenance record](../reports/ruff-cleanup-v1/README.md) adds clean lint/format checks, 16 passing tests, and a complete replay with all 126 comparator dossiers and four recorded pilot replays matching.

Verified 2026-10-24 14:27 PDT · local release 0.1.0

The first iPSC expansion-and-banking investigation is complete as a local research simulator. Its source, interface, executed comparisons, recorded model pilot, failure analysis and reproduction commands are retained. GitHub setup and publication remain deferred.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Engine and HTTP tests | 13 passed; no failures | [Test output](../reports/verification-final-tests.txt) |
| Retained scientific-source and artifact checks | Passed for all 126 comparator campaigns, four pilot episodes and 44 model decisions | [Artifact checks](../reports/verification-final-artifacts.json) |
| Fresh comparator reconstruction | 126/126 metric and decision matches; 126/126 dossiers identical | [Reproduction result](../reports/reproduction-v1/RESULT.json) |
| Recorded model-action replay | All four observation sequences and dossiers identical; zero new model calls | [Reproduction result](../reports/reproduction-v1/RESULT.json) |
| Frontend syntax | Passed `node --check web/app.js` | [Check record](../reports/development-verification.json) |
| Browser downloads | Downloaded dossier equals local API dossier; both CSV sample rows match every exported field | [Dossier](../reports/browser-dossier.json), [CSV](../reports/browser-samples.csv) |
| Mobile breakpoint | Campaign and study views checked at 390 × 844 px; document width 390 px in both views; temporary override reset | [Mobile campaign](../reports/mobile-campaign-screen.png) |

Browser testing covered the five laboratory views, delayed and invalid samples, repeat collection with the invalid record retained, campaign branching, a bounded perfusion change, rejection of a pump intervention without its required check, saved-session reload, and export downloads. These are bounded workflow checks, not a full accessibility or cross-browser certification. Desktop and mobile screenshots preserve the inspected layouts.

The browser download-event watcher timed out even though Chrome saved the files. Verification therefore used the actual downloaded JSON and CSV bytes and compared them with the application records. The downloaded examples are retained above.

## What remains limited

All process histories and QC results are synthetic. The model coefficients are illustrative and are not fitted to raw experimental campaigns. The source audit did not obtain synchronized sensor/action/QC records. Material-accounting and numerical tests establish the tested simulator behavior; they do not establish biological prediction or manufacturing transfer.

The four-episode pilot records real choices by the active developer-model. It is an informed pilot, with higher medium use and a different decision cadence from the rule comparator. It does not demonstrate an independent autonomous LLM service or AI superiority.

The reporting bank retains four unsafe simulated accepts across the three policies. They expose a checkpoint-to-endpoint evidence gap: passing QC at 114 h can precede endpoint viability below the illustrative minimum. See the [investigation](INVESTIGATION.md). This is a retained scientific finding, not a claim that the simulation contract guarantees correct disposition.

## Handoff

Start with `python3 -m ipsc_lab.server --port 8840` from the project root, or open `run.command` on macOS. The server is loopback-only. Interactive sessions persist separately in the ignored `.runtime/` folder. The development preview is stopped at handoff; launching the application restores those sessions.

[Reproducibility instructions](REPRODUCIBILITY.md) describe tests, source bindings and replay. `SHA256SUMS` covers the delivered source, documentation and retained public evidence, excluding local Git metadata, runtime sessions, interpreter caches and private pilot working state. It excludes itself.

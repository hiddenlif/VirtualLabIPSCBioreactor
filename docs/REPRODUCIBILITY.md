# Reproduce and inspect the work

Run commands from the project root with Python 3.10 or newer. Development verification used Python 3.13 on macOS ARM64. No third-party runtime package or network connection is required.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/verify_results.py
python3 scripts/reproduce.py --out reports/reproduction-check
```

Choose another new output path for a later reproduction. Existing results are never overwritten. The original one-time reporting command, `python3 scripts/evaluate.py`, deliberately refuses its already-existing `reports/comparison-v1/` directory.

## What each command does

- The tests check material and cell accounting, delayed availability, passive observation, public/latent separation, numerical refinement, valid/invalid/stale evidence, action atomicity and idempotence, branching, causal fault effects, and local HTTP behavior.
- `verify_results.py` independently recalculates retained summary statistics from the CSV, checks the complete reporting roster, verifies every dossier digest and scientific-source binding, and checks the pilot trace inventory. It does not rerun a model.
- `reproduce.py` reconstructs all 126 campaigns from the frozen plan, compares their metrics with the retained results, then replays all 44 recorded model decisions. It does not obtain new model outputs. It reports exact content agreement separately from numerical agreement.

## Evidence files

`reports/comparison-v1/PLAN.json` pins source hashes and the full reporting design. `metrics.csv` contains one row for each scenario/seed/policy combination. `campaigns.jsonl` stores those metrics with each public campaign dossier. `summary.json` contains the descriptive aggregates.

`runs/model-pilot-v1/RULE.json` binds the pilot design. The public folder retains observations, compact model-visible renderings, model-authored decision files, and their executed copies. `actions.json` contains the complete ordered action history. `reports/model-pilot-v1/unmasked-plan.json` supports reproducibility after evaluation; these cases must not be described as unseen to a future model that can read this repository.

`reports/model-pilot-v1/*-dossier.json` preserves each completed pilot. The summary includes matched fixed, feedback and diagnostic-rule outcomes. A replay is a deterministic re-execution of these existing decisions, not an additional AI experiment.

## Runtime and exports

Start the application with `python3 -m ipsc_lab.server --port 8840`. Sessions are separate from retained study artifacts and persist in `.runtime/`. The UI's **New campaign** and **Branch** operations create additional interactive experiments; they do not alter the frozen reporting bank.

The dossier export contains the SOP, public observations, assay and action histories, evidence-based conclusion, and an observation digest. The CSV export contains only sampled records. Pending samples do not expose their hidden future values. The server and interface run locally; there are no external scientific-tool, LLM-service, actuator, or manufacturing-system connections.

## Provenance limits

The scientific-source hashes freeze the implementation used by the original reporting study. The Ruff maintenance revision preserves those original reports and records an explicit original-to-current source hash mapping in `reports/ruff-cleanup-v1/source-revision.json`. Verification accepts the original implementation or that exact recorded revision; unrecorded source changes fail. The cleanup's tests and complete campaign/model-action replay are retained beside the mapping. This records maintenance provenance without rewriting the study's original source hashes.

Documentation and frontend-only edits do not change that science manifest. Full project file checksums are recorded separately at delivery. Reproduction on a different Python/platform may produce tiny floating-point differences; these are distinguished from exact digest agreement and substantive metric disagreement.

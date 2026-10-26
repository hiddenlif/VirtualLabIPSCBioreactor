# Can a supervisory workflow make better process and evidence decisions?

This completed first investigation concerns a documented synthetic iPSC expansion-and-banking environment. It evaluates conventional controls across a fixed reporting bank and records a separate, informed Codex decision pilot. It does not test a calibrated patient/product-specific digital twin, prospective manufacturing performance, or an independently deployed autonomous AI system.

## Design and actual execution

The comparator plan was frozen before reporting runs. Development used seeds 17, 29 and 43. Reporting used seeds 101, 107, 113, 127, 131 and 139, across all seven scenario families and all three policies: **126 campaigns**. Initial parameters and keyed measurement-noise rules match across policies. Actual observation times differ when policies sample at different times.

The fixed schedule keeps the initial perfusion command and collects scheduled measurements. Conventional feedback uses sampled glucose, a mass-balance feed-forward term and a proportional correction. The diagnostic rule supervisor adds independent instrument checks, repeats invalid samples, and performs evidence-supported calibration or delivery service. All three are conventional software comparators, not LLM outputs.

The acting workflow receives public observations; the evaluator separately retains latent parameters and true endpoint quality. The public accept/hold/reject recommendation follows the versioned evidence contract. The latent screen examines modeled endpoint quality and cumulative adverse exposure. Disagreement is decomposed into unsafe acceptance, conservative holding, and other differences.

## Comparator results

| Policy | Campaigns | Mean yield, million viable cells | Mean medium, mL | Mean adverse exposure, h | Public/latent agreement | Unsafe accepts |
|---|---:|---:|---:|---:|---:|---:|
| Fixed schedule | 42 | 314.3 | 318.3 | 21.9 | 40/42 | 2 |
| Conventional feedback | 42 | 387.4 | 507.5 | 21.9 | 41/42 | 1 |
| Diagnostic rules | 42 | 434.9 | 532.3 | 2.5 | 41/42 | 1 |

There were no public holds on latent-accept campaigns in this reporting bank. That does not establish a zero false-hold rate. The always-hold counterfactual is reported separately by the verification script to show how many eligible campaigns it would unnecessarily withhold.

The diagnostic rule policy reduced mean adverse exposure in this simulator, especially by correcting pH bias. It also used more medium than the fixed schedule. Mean yield alone is insufficient to choose a policy: quality, evidence completeness, historical exposure and cost remain visible.

## A retained failure: the QC window can miss late deterioration

Four policy/campaign combinations accepted despite failing the latent endpoint screen:

| Scenario | Seed | Policy | Viability at 114 h QC | True endpoint viability |
|---|---:|---|---:|---:|
| Routine | 131 | Fixed | 0.8683 | 0.84569 |
| Invalid sample | 131 | Fixed | 0.8683 | 0.84569 |
| Delivery loss | 131 | Feedback | 0.8577 | 0.84285 |
| Delivery loss | 131 | Diagnostic rules | 0.8577 | 0.84285 |

The illustrative minimum is 0.85. These are not four independent biological discoveries; two pairs share the same relevant modeled trajectory. The software correctly enforced its declared checkpoint contract, but that contract and the sampling policy did not fully establish endpoint quality. This is an evidence-coverage failure, not a floating-point problem or an invalid assay.

The frozen study and SOP remain unchanged so the result is inspectable. A future prospective study could compare later collection, repeated viability checks, or a defined trend-based rule under the same control budget. No claim that a particular replacement contract is validated follows from proposing it.

## Actual Codex pilot

Four campaign families (routine, probe drift, delivery loss and demand shift) were assigned to masked episode labels and separate seeds before model decisions. Each started after the same 48 h routine warm-up. The primary Codex conversation made **44 actual decisions**, retained with rationales, evidence citations, observation digests and simulator outputs. No external model API was called by the recording script.

The developer-model knew the simulator design and the four possible families. The initial mapping was masked, but this was **not an independent blind trial**. The exact model identifier and reasoning setting were not supplied by the runtime. The first public input was read in full; later compact renderings are retained beside their complete available observations.

The pilot identified a reference-pH discrepancy in A and corrected calibration, identified low delivery in B and verified service, left C without an invented fault, and treated D's metabolic trend as a demand hypothesis after normal delivery evidence. It collected banking QC at 118 h, waited for delayed channels, and made final recommendations after reviewing all five results.

| Episode / family | Model yield, million cells | Diagnostic-rule yield | Model medium, mL | Diagnostic-rule medium | Model adverse exposure, h | Final recommendation / latent screen |
|---|---:|---:|---:|---:|---:|---|
| A / probe drift | 587.4 | 507.4 | 796.0 | 581.6 | 13.0 | Hold / hold |
| B / delivery loss | 588.5 | 428.3 | 771.4 | 332.8 | 0.0 | Accept / accept |
| C / routine | 585.9 | 533.9 | 795.7 | 619.5 | 0.0 | Accept / accept |
| D / demand shift | 505.8 | 469.0 | 895.8 | 784.3 | 0.0 | Accept / accept |

Fresh execution of the retained actions reproduced all four final dossiers exactly. That validates replay consistency, not independent biological correctness. All pilot outcomes and all 12 matched conventional-policy comparisons are retained.

The pilot's higher yields came with higher medium use and a different action cadence. The total medium allowance did not bind any reported policy. The inventory ledger also provided an early delivery clue. Consequently, these four cases do not establish superior reasoning efficiency, optimal measurement allocation, intrinsic diagnostic difficulty, or an LLM advantage over an equally informed and budget-matched conventional policy.

## What the first investigation establishes

The laboratory completes a real software workflow: observe, gather delayed evidence, investigate competing explanations, intervene, preserve history, and produce a reproducible disposition dossier. The executed comparison exposes where a plausible evidence contract remains insufficient. The model pilot demonstrates actual evidence-linked decisions while keeping its knowledge and evaluation limitations explicit.

Empirical calibration, broader biological variation, independent autonomous-model evaluation, functional pluripotency, differentiated-product manufacturing, larger vessels, positive microbial-fault cases and external validation are outside this version's completed scope.

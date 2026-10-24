# Process and evidence model, version 0.1.0

This model supports a software investigation of observation, diagnosis, intervention, and disposition. Its coefficients and quality thresholds are illustrative assumptions. The cited literature motivates the process variables; the implementation does not reproduce or fit the published authors' model.

## State and units

| Quantity | Representation | Initial condition |
|---|---|---|
| Culture volume | L, held constant | 0.15 L |
| Viable and dead cells | million cells | 75 and 2 |
| Glucose inventory | g | 0.90 |
| Lactate inventory | g | 0.015 |
| True pH and dissolved oxygen | pH; % air saturation | 7.05; 40 |
| Commanded perfusion | mL/h | 3 |
| Available medium and sample allowance | mL | 2,000 and 18 |

The culture runs to 120 h. After that endpoint, only the evidence clock advances; the model does not simulate cryopreservation, storage, continued growth, or post-bank deterioration. Qualifying QC is collected from 114 h until just before 120 h. The normal evidence closeout is 156 h; manual exploration is allowed through 168 h.

## Material and cell accounting

Fresh medium contains an assumed 6 g/L glucose. Perfusion adds and removes equal volumes, retaining cells. For delivered flow Q in L/h, integration interval Δt, and culture volume V:

- Glucose input is `Q × 6 × Δt` g.
- Glucose and lactate removal are `Q × concentration × Δt` g.
- Glucose consumption is `qG × viable_cells × demand_multiplier × Δt`, capped by available inventory.
- Lactate production is an assumed `1.6 × glucose_consumption` by mass.

A sample removes its volume fraction of viable cells, dead cells, glucose and lactate. Replacement medium restores volume, adds glucose, and counts toward medium use. The ledger retains every input, output, consumption, growth, death, and sample withdrawal. Tests independently reconstruct four accounting identities from the initial condition and those accumulated terms.

This is not a full elemental, carbon, energy, or oxygen mass balance. Lactate is the only modeled product of glucose consumption. No claim of whole-metabolism conservation follows from the implemented inventory checks.

## Growth and process control

The assumed maximum growth rate is drawn reproducibly between 0.030 and 0.038 per hour. Glucose demand is drawn between 0.000026 and 0.000034 g per million viable cells per hour. Neither range is fitted to experimental campaign records.

Growth includes an initial lag, a glucose saturation term, lactate inhibition, and a carrying-capacity term. Death increases under assumed glucose, lactate, pH and oxygen stress. Dead cells accumulate in this simplified retained-cell model and are removed only by sampling.

The conventional pH loop relaxes toward its target with a 1.5 h response time. An online pH bias changes the true controlled state. Oxygen control has a finite modeled capacity: increasing biomass and metabolic demand can reduce the achievable oxygen level. This is a first-order surrogate, not a gas-transfer or aggregate-scale oxygen-diffusion model. Supervisory actions do not include changing oxygen-transfer hardware, agitation, harvest time, or vessel scale.

Integration uses 0.25 h explicit steps. Steps split at fault onset, assay completion and the culture endpoint. Tests compare selected development campaigns against 0.125 h integration, requiring relative viable-yield disagreement below 1.5% and glucose-inventory disagreement below 0.01 g. These are bounded numerical checks, not a continuous-domain proof.

## Measurements and causal disturbances

Online pH, dissolved oxygen and temperature carry keyed synthetic noise. Glucose, lactate, viable density, viability, aggregate diameter and independent pH arrive only as delayed samples. Aggregate diameter is an illustrative biomass-based descriptor; shear stress and functional cell quality are not measured.

| Scenario | Implemented change |
|---|---|
| Routine | Biological parameter variation only |
| Probe drift | +0.28 online pH bias after a seeded onset; affects the fast loop until recalibration |
| Delivery loss | Actual flow falls to 32% of command until service |
| Demand shift | Glucose demand multiplier rises to 2.1 |
| Invalid sample | First post-onset metabolic sample fails integrity control and carries an altered lactate reading |
| Genomic flag | Independent simulated genomic screen returns a valid failing category |
| Combined | Probe, delivery and demand disturbances overlap |

Onset is drawn from 34, 38 or 42 h. Independent delivery and calibration checks have one-hour delays. Metabolic panels have two-hour delays. Sampling consumes finite material even when invalid.

The medium ledger reports actual simulated consumption. It is an auxiliary delivery signal: comparing consumption with commands can suggest delivery loss before an explicit flow check. The pilot used that signal. The experiment therefore does not establish that delivery verification is indispensable or that root-cause identification is intrinsically difficult.

## Quality interpretation

`config/sop.json` is the authoritative project contract. Identity, phenotype, viability, genomic and microbial evidence are separate simulated channels. Phenotype is a marker-like undifferentiated-state descriptor, not functional pluripotency. The genomic and microbial categories are simplified screen outcomes. There is no positive microbial-fault scenario in the current bank.

The public disposition interpreter uses available records only. It checks batch identity, assay version, validity, collection checkpoint, result arrival and numerical/category requirements. Any qualifying valid failure remains consequential, including after a later passing record. Missing or ineligible evidence causes hold. A recorded excursion or historical sensor discrepancy also causes hold. This version has no automatic history-issue clearance or investigation sign-off action.

The evaluator separately inspects true endpoint quality and cumulative latent adverse exposure. Its endpoint screen returns reject for a failing modeled quality value, hold for more than four hours of latent adverse exposure, and accept otherwise. That screen is another declared simulation assumption, not biological ground truth or an established release standard.

## Boundary and persistence

Acting observations exclude scenario identity, latent parameters, onset and future sample values. The evaluator has a separate method and retained source records. This is a code/API separation for research; the local filesystem is not an adversarial secrecy boundary.

Actions validate numerical finiteness, limits, sample/material allowance, eligible evidence citations and intervention prerequisites. Draft-state execution makes action batches atomic. Reused action IDs are idempotent and cannot be reused for different content. Branches are deep copies. Public observations are copies and cannot mutate the simulator.

The local server requires its in-memory session token and a loopback Host/Origin for mutations. It serves static files only from `web/`. These protections support a local app; it has not been designed or audited as an internet-facing service.

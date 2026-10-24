"""Retain the exact compact public-input rendering shown to the primary model."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"runs/model-pilot-v1/public"
rows=json.loads((root/"current-input.json").read_text());log=json.loads((root/"actions.json").read_text())
rendered=[]
for row in rows:
    o=row["observation"]
    sampled=[s for s in o["samples"] if s["collected_h"]>=max(0,o["time_h"]-26) or s["assay"]!="metabolic"]
    rendered.append(dict(id=row["id"],input_sha256=row["input_sha256"],time_h=o["time_h"],flow=o["settings"]["perfusion_ml_h"],resources=o["resources"],assessment=o["assessment"],
        telemetry=[{k:r[k] for k in ("time_h","ph","do_pct")} for r in o["telemetry"][-3:]],
        samples=[{k:s[k] for k in ("id","assay","collected_h","result_h","status","valid","values") if k in s} for s in sampled],
        recent_interventions=[e for e in o["events"] if e["kind"] in ("intervention","recommendation")]))
(root/f"step-{len(log)+1:02d}-model-visible.json").write_text(json.dumps(rendered,indent=2))
print(json.dumps(rendered,indent=2))

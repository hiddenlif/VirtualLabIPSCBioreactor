"""Reconstruct the frozen simulator bank and replay existing model actions."""
import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ipsc_lab.engine import digest
from ipsc_lab.policies import run
from evaluate import source_hashes
from model_pilot import warm,payload


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",required=True);args=parser.parse_args()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    source=ROOT/"reports/comparison-v1"
    plan=json.loads((source/"PLAN.json").read_text())
    if source_hashes()!=plan["source_hashes"]:raise ValueError("Scientific sources differ from the frozen reporting design")
    rows=list(csv.DictReader((source/"metrics.csv").open()))
    matches=[]
    for r in rows:
        c=run(r["scenario"],int(r["seed"]),r["policy"])
        t=c.truth_summary()
        numeric={k:math.isclose(t[k],float(r[k]),rel_tol=1e-10,abs_tol=1e-8) for k in ("yield_million_cells","viability","adverse_exposure_h","medium_used_ml","sample_used_ml")}
        decisions=t["public_decision"]==r["public_decision"] and t["latent_quality_decision"]==r["latent_quality_decision"]
        matches.append(dict(scenario=r["scenario"],seed=int(r["seed"]),policy=r["policy"],numerically_equivalent=all(numeric.values()),
                            decisions_equal=decisions,dossier_exact=digest(c.dossier())==r["dossier_sha256"]))
    pilot=ROOT/"reports/model-pilot-v1"
    design=json.loads((pilot/"unmasked-plan.json").read_text())
    log=json.loads((ROOT/"runs/model-pilot-v1/public/actions.json").read_text())
    expected=json.loads((pilot/"summary.json").read_text())
    replay=[]
    for e in design["cases"]:
        c=warm(e["scenario"],e["seed"],"PILOT-"+e["id"]);inputs=True
        for stage in log:
            inp=next(x for x in stage["observed"] if x["id"]==e["id"])
            inputs=inputs and digest(payload(c))==inp["input_sha256"]
            r=next(x for x in stage["decisions"] if x["id"]==e["id"])
            c.action(r.get("commands",[]),r.get("advance_h",0),r["rationale"],r.get("evidence",[]),actor="Codex supervisor (interactive)")
        target=next(x for x in expected["episodes"] if x["id"]==e["id"])
        replay.append(dict(id=e["id"],observation_sequence_exact=inputs,dossier_exact=digest(c.dossier())==target["dossier_sha256"]))
    ok=all(m["numerically_equivalent"] and m["decisions_equal"] for m in matches) and all(m["observation_sequence_exact"] and m["dossier_exact"] for m in replay)
    result=dict(status="PASS" if ok else "FAIL",created_at=subprocess.check_output(["date","+%Y-%m-%d %H:%M %Z"],text=True).strip(),
                campaign_count=len(matches),numerically_equivalent=sum(m["numerically_equivalent"] for m in matches),
                decisions_equal=sum(m["decisions_equal"] for m in matches),dossiers_exact=sum(m["dossier_exact"] for m in matches),
                model_replays=replay,new_model_calls=0,scientific_source_hashes=source_hashes())
    (out/"campaign-checks.json").write_text(json.dumps(matches,indent=2))
    (out/"RESULT.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));sys.exit(0 if ok else 1)


if __name__=="__main__":main()

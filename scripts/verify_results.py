"""Verify retained artifacts without creating new scientific or model runs."""
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ipsc_lab.engine import digest
from evaluate import source_hashes


def check():
    out=ROOT/"reports/comparison-v1"
    plan=json.loads((out/"PLAN.json").read_text());summary=json.loads((out/"summary.json").read_text())
    assert source_hashes()==plan["source_hashes"],"Scientific source binding changed"
    assert digest(plan)==summary["plan_sha256"],"Plan digest mismatch"
    rows=list(csv.DictReader((out/"metrics.csv").open()))
    roster={(s,str(seed),p) for s in plan["scenarios"] for seed in plan["seeds"] for p in plan["policies"]}
    assert len(rows)==126 and {(r["scenario"],r["seed"],r["policy"]) for r in rows}==roster
    raw=[json.loads(line) for line in (out/"campaigns.jsonl").read_text().splitlines()]
    assert len(raw)==126
    for row,r in zip(rows,raw):
        assert digest(r["dossier"])==row["dossier_sha256"]==r["metrics"]["dossier_sha256"]
        assert digest(r["dossier"]["campaign"])==r["dossier"]["observation_sha256"]
        for k,v in r["metrics"].items():
            if isinstance(v,float):assert math.isclose(float(row[k]),v,abs_tol=1e-12)
            else:assert row[k]==str(v)
    for s in summary["summary"]:
        rr=[r for r in rows if r["policy"]==s["policy"]]
        for field,metric in (("mean_yield_million","yield_million_cells"),("mean_media_ml","medium_used_ml"),("mean_adverse_h","adverse_exposure_h")):
            assert math.isclose(s[field],statistics.mean(float(r[metric]) for r in rr),abs_tol=1e-10)
        for field,metric in (("decision_agreement","public_latent_agreement"),("unsafe_accepts","unsafe_accept"),("unnecessary_holds","unnecessary_hold")):
            assert s[field]==sum(r[metric]=="True" for r in rr)
    p=ROOT/"reports/model-pilot-v1"
    pilot=json.loads((p/"summary.json").read_text());unmasked=json.loads((p/"unmasked-plan.json").read_text())
    rule=json.loads((ROOT/"runs/model-pilot-v1/RULE.json").read_text())
    log=json.loads((ROOT/"runs/model-pilot-v1/public/actions.json").read_text())
    assert digest(unmasked)==pilot["plan_sha256"]==rule["plan_sha256"]
    assert pilot["source_hashes"]==source_hashes()
    assert len(log)==11 and pilot["decision_count"]==44 and pilot["n"]==4
    for stage in log:
        assert sorted(r["id"] for r in stage["decisions"])==list("ABCD")
        for inp in stage["observed"]:assert digest(inp["observation"])==inp["input_sha256"]
    for e in pilot["episodes"]:
        d=json.loads((p/(e["id"]+"-dossier.json")).read_text())
        assert digest(d)==e["dossier_sha256"]
        assert d["campaign"]["time_h"]==156 and e["replay_identical"]
        assert len(e["baselines"])==3
    counts={policy:sum(r["latent_quality_decision"]=="accept" for r in rows if r["policy"]==policy) for policy in plan["policies"]}
    return dict(status="PASS",comparator_campaigns=126,pilot_episodes=4,actual_model_decisions=44,
                scientific_sources_match=True,dossiers_and_aggregates_match=True,
                always_hold_eligible_campaigns_withheld=counts,
                scope="Artifact integrity and numerical reproduction of retained summaries; no new model calls")


if __name__=="__main__":print(json.dumps(check(),indent=2))

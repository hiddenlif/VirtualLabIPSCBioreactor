"""Frozen matched comparator study. Standard library only; one worker."""
import csv
import hashlib
import json
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ipsc_lab.engine import SCENARIOS, digest
from ipsc_lab.policies import POLICIES, run


def source_hashes():
    files=sorted([*ROOT.glob("ipsc_lab/*.py"),*ROOT.glob("config/*.json"),Path(__file__)])
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main():
    out=ROOT/"reports"/"comparison-v1"
    out.mkdir(exist_ok=False)
    seeds=[101,107,113,127,131,139]
    plan=dict(design="Matched synthetic campaigns; all scenarios and seeds reported",seeds=seeds,
              development_seeds=[17,29,43],policies=POLICIES,scenarios=list(SCENARIOS),
              model_runs=0,source_hashes=source_hashes(),primary_endpoints=["latent/public disposition mismatch","yield_million_cells","adverse_exposure_h","medium_used_ml"],
              limitations=["Held-out seeds, not an independent biological validation", "Rule supervisors are conventional comparators, not AI outputs", "Descriptive comparison; no significance or real-world prediction claim"])
    (out/"PLAN.json").write_text(json.dumps(plan,indent=2))
    rows=[]
    with (out/"campaigns.jsonl").open("w") as f:
        for scenario in SCENARIOS:
            for seed in seeds:
                for policy in POLICIES:
                    c=run(scenario,seed,policy)
                    truth=c.truth_summary()
                    row=dict(scenario=scenario,seed=seed,policy=policy,**{k:v for k,v in truth.items() if k not in ("scenario","seed","balances","mu_h","qg","onset_h")},
                             public_latent_agreement=truth["public_decision"]==truth["latent_quality_decision"],
                             unsafe_accept=truth["public_decision"]=="accept" and truth["latent_quality_decision"]!="accept",
                             unnecessary_hold=truth["public_decision"]=="hold" and truth["latent_quality_decision"]=="accept",
                             balance_max_abs=max(abs(v) for v in truth["balances"].values()),
                             dossier_sha256=digest(c.dossier()))
                    rows.append(row)
                    f.write(json.dumps(dict(metrics=row,dossier=c.dossier()),sort_keys=True)+"\n")
    fields=list(rows[0])
    with (out/"metrics.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    summary=[]
    for policy,label in POLICIES.items():
        rr=[r for r in rows if r["policy"]==policy]
        summary.append(dict(policy=policy,label=label,n=len(rr),mean_yield_million=statistics.mean(r["yield_million_cells"] for r in rr),
            mean_media_ml=statistics.mean(r["medium_used_ml"] for r in rr),mean_adverse_h=statistics.mean(r["adverse_exposure_h"] for r in rr),
            decision_agreement=sum(r["public_latent_agreement"] for r in rr),unsafe_accepts=sum(r["unsafe_accept"] for r in rr),
            unnecessary_holds=sum(r["unnecessary_hold"] for r in rr),max_balance_residual=max(r["balance_max_abs"] for r in rr)))
    result=dict(created_at=subprocess.check_output(["date","+%Y-%m-%d %H:%M %Z"],text=True).strip(),plan_sha256=digest(plan),campaign_count=len(rows),summary=summary,
                ai_runs=0,scope="Executed synthetic comparator study; AI pilot is recorded separately")
    (out/"summary.json").write_text(json.dumps(result,indent=2))
    lines=["# Executed comparator study", "",f"{len(rows)} campaigns: seven scenarios × six held-out seeds × three conventional policies.","",
           "| Policy | Mean yield (million cells) | Mean medium (mL) | Mean adverse exposure (h) | Public/latent agreement | Unsafe accepts | Unnecessary holds |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for r in summary:
        lines.append(f"| {r['label']} | {r['mean_yield_million']:.1f} | {r['mean_media_ml']:.1f} | {r['mean_adverse_h']:.1f} | {r['decision_agreement']}/{r['n']} | {r['unsafe_accepts']} | {r['unnecessary_holds']} |")
    lines.extend(["","The latent decision is an evaluator-only physical-quality screen. The public decision applies the evidence contract. A discrepancy can expose undetected harm, or a justified conservative hold; these are reported separately. An accept with latent harm is a failure.","",
        "The analysis is descriptive. Policies share initial parameters and keyed measurement noise, but different sampling times produce different observations. No policy was retuned on these reporting seeds. These synthetic results do not establish benefit in real iPSC manufacturing, biological generalization, or an LLM advantage."])
    (out/"REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()

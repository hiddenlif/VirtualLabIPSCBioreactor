"""Record real in-session model actions, then reproduce and compare them.

This is an informed developer-model pilot, not an independent cold experiment.
No model service is called by this script. Actions come from the active Codex
conversation, whose exact model/effort are not exposed to this script.
"""
import argparse
import copy
import json
import secrets
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ipsc_lab.engine import Campaign,digest
from ipsc_lab.policies import commands,POLICIES
from evaluate import source_hashes

OUT=ROOT/"runs/model-pilot-v1"


def write(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False))
def load_campaign(path):
    c=Campaign.__new__(Campaign);c.__dict__.update(json.loads(path.read_text()));return c
def warm(scenario,seed,label):
    c=Campaign(scenario,seed,label=label)
    for _ in range(24):c.action(commands(c.observation(),"fixed"),advance_h=2,actor="fixed",rationale="Common fixed-schedule warm-start")
    return c
def payload(c):
    o=c.observation()
    return {k:o[k] for k in ("batch","time_h","process_end_h","sop","evidence_layer","resources","settings","assessment")}|dict(
        telemetry=o["telemetry"][-13:],samples=o["samples"],events=o["events"][-10:])
def state_path(key):return OUT/"private"/(key+".json")


def prepare():
    OUT.mkdir(exist_ok=False);(OUT/"private").mkdir();(OUT/"public").mkdir()
    cases=["nominal","probe_drift","delivery_loss","demand_shift"]
    secrets.SystemRandom().shuffle(cases)
    plan=dict(cases=[dict(id=key,scenario=scenario,seed=seed) for key,scenario,seed in zip("ABCD",cases,[211,223,227,229])],
              source_hashes=source_hashes(),created_at=subprocess.check_output(["date","+%Y-%m-%d %H:%M %Z"],text=True).strip(),
              warm_start_h=48,closeout_h=156,comparators=list(POLICIES),
              model_provenance="Active Codex primary conversation; exact model and effort not provided by runtime",
              limitation="The developer-model knows the simulator design. Scenario mapping is masked until closeout; this is not independent blinding.")
    write(OUT/"private/PLAN.json",plan)
    rule=dict(plan_sha256=digest(plan),n=4,scenario_families=sorted(cases),protocol="Observe public payload, retain each actual model decision, execute bounded actions, recommend at closeout, then unmask and compare. No automated model or API call.",
              rule="Every episode and failure is retained; no quantitative advantage or generalization threshold is set.",
              endpoints=["yield","media","adverse exposure","proposed/public/latent disposition","evidence citation validity"],
              source_hashes=plan["source_hashes"],limitation=plan["limitation"])
    write(OUT/"RULE.json",rule)
    for e in plan["cases"]:write(state_path(e["id"]),warm(e["scenario"],e["seed"],"PILOT-"+e["id"]).__dict__)
    write(OUT/"public/actions.json",[])
    print(json.dumps(rule,indent=2))


def observe():
    rows=[]
    for key in "ABCD":
        o=payload(load_campaign(state_path(key)))
        rows.append(dict(id=key,input_sha256=digest(o),observation=o))
    write(OUT/"public/current-input.json",rows)
    print(json.dumps(rows,indent=2))


def act(file):
    requested=json.loads(Path(file).read_text())
    if not isinstance(requested,list) or sorted(r["id"] for r in requested)!=list("ABCD"):
        raise ValueError("Supply one decision for each of A, B, C, D")
    current=json.loads((OUT/"public/current-input.json").read_text())
    log=json.loads((OUT/"public/actions.json").read_text())
    staged=[]
    for row in requested:
        c=load_campaign(state_path(row["id"]));o=payload(c)
        expected=next(r["input_sha256"] for r in current if r["id"]==row["id"])
        if digest(o)!=expected:raise ValueError("Observation changed; observe again")
        c.action(row.get("commands",[]),advance_h=row.get("advance_h",0),rationale=row["rationale"],
                 evidence=row.get("evidence",[]),actor="Codex supervisor (interactive)")
        staged.append((row["id"],c))
    step=len(log)+1
    write(OUT/"public"/f"step-{step:02d}-input.json",current)
    write(OUT/"public"/f"step-{step:02d}-model-output.json",requested)
    log.append(dict(step=step,observed=current,decisions=requested))
    write(OUT/"public/actions.json",log)
    for key,c in staged:write(state_path(key),c.__dict__)
    print(json.dumps(dict(step=step,times={key:c.clock for key,c in staged}),indent=2))


def finish():
    plan=json.loads((OUT/"private/PLAN.json").read_text())
    hashes=source_hashes()
    if hashes!=plan["source_hashes"]:raise ValueError("Scientific source changed after freeze")
    log=json.loads((OUT/"public/actions.json").read_text())
    report=ROOT/"reports/model-pilot-v1";report.mkdir(exist_ok=False)
    episodes=[]
    for item in plan["cases"]:
        key=item["id"];c=load_campaign(state_path(key))
        if c.clock!=156:raise ValueError("Complete every episode to 156 h")
        recs=[e for e in c.events if e["kind"]=="recommendation"]
        if not recs:raise ValueError("Record the model's proposed disposition")
        proposed=recs[-1]["title"].split(": ")[-1].lower()
        replay=warm(item["scenario"],item["seed"],"PILOT-"+key)
        for stage in log:
            inp=next(x for x in stage["observed"] if x["id"]==key)
            if digest(payload(replay))!=inp["input_sha256"]:raise ValueError("Replay input mismatch")
            r=next(x for x in stage["decisions"] if x["id"]==key)
            replay.action(r.get("commands",[]),r.get("advance_h",0),r["rationale"],r.get("evidence",[]),actor="Codex supervisor (interactive)")
        if digest(replay.dossier())!=digest(c.dossier()):raise ValueError("Independent replay mismatch")
        baselines=[]
        for policy in POLICIES:
            b=warm(item["scenario"],item["seed"],"PILOT-"+key)
            while b.clock<156:b.action(commands(b.observation(),policy),min(2,156-b.clock),POLICIES[policy],actor=policy)
            baselines.append(dict(policy=policy,**b.truth_summary()))
        t=c.truth_summary();rule=next(x for x in baselines if x["policy"]=="diagnostic")
        episodes.append(dict(id=key,scenario=item["scenario"],seed=item["seed"],model_yield_million=t["yield_million_cells"],rule_yield_million=rule["yield_million_cells"],
                             model_media_ml=t["medium_used_ml"],model_adverse_h=t["adverse_exposure_h"],proposed_disposition=proposed,
                             public_decision=t["public_decision"],latent_decision=t["latent_quality_decision"],baselines=baselines,
                             replay_identical=True,dossier_sha256=digest(c.dossier())))
        write(report/(key+"-dossier.json"),c.dossier())
    summary=dict(n=len(episodes),decision_count=len(log)*4,provenance=plan["model_provenance"],
                 plan_sha256=digest(plan),source_hashes=hashes,episodes=episodes,
                 limitations=[plan["limitation"],"Four purposive synthetic cases; no statistical or biological generalization.","No independent autonomous LLM system was evaluated; these are actual choices made in the active Codex session.","The rule comparator operates every 2 h; the model chooses its decision intervals. All costs and sample timing are retained."],
                 proposed_latent_agreement=sum(e["proposed_disposition"]==e["latent_decision"] for e in episodes),
                 proposed_public_agreement=sum(e["proposed_disposition"]==e["public_decision"] for e in episodes))
    write(report/"summary.json",summary)
    write(report/"unmasked-plan.json",plan)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["prepare","observe","act","finish"]);p.add_argument("--file");a=p.parse_args()
    {"prepare":prepare,"observe":observe,"act":lambda:act(a.file),"finish":finish}[a.mode]()

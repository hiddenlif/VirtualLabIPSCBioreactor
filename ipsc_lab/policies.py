"""Transparent conventional comparators. None of these policies is an LLM."""
from .engine import Campaign,SOP

POLICIES = {
    "fixed": "Fixed schedule",
    "feedback": "Conventional feedback",
    "diagnostic": "Evidence-seeking supervisor (rules)",
}


def latest(obs, assay, valid=True):
    rows=[s for s in obs["samples"] if s["assay"]==assay and s["status"]=="complete" and (s["valid"] or not valid)]
    return max(rows,key=lambda s:(s["collected_h"],s["id"])) if rows else None


def pending(obs, assay):
    return any(s["assay"]==assay and s["status"]=="pending" for s in obs["samples"])


def commands(obs, policy):
    if policy not in POLICIES:
        raise ValueError("Unknown policy")
    t=obs["time_h"]
    if t>=120:
        return []
    out=[]
    schedule=24 if policy=="fixed" else 12
    met=latest(obs,"metabolic",valid=False)
    if t>0 and (not met or t-met["collected_h"]>=schedule) and not pending(obs,"metabolic"):
        out.append(dict(type="sample",panel="metabolic"))
    # One full panel, collected at the banking checkpoint.
    if t>=SOP["qc_checkpoint_h"] and not any(s["assay"]=="identity" and s["collected_h"]>=SOP["qc_checkpoint_h"] for s in obs["samples"]):
        out.append(dict(type="sample",panel="qc"))
    if policy=="fixed":
        return out
    m=latest(obs,"metabolic")
    if m:
        v=m["values"]
        density=v["viable_cell_density_m_ml"]
        # Mass-balance feed-forward plus a proportional correction from sampled glucose.
        target=max(2,min(12, density*150*.00003/2.5*1000+1.6*(3.5-v["glucose_g_l"])))
        if v["lactate_g_l"]>1.8:
            target=min(12,max(target,obs["settings"]["perfusion_ml_h"]+1))
        if abs(target-obs["settings"]["perfusion_ml_h"])>.4:
            out.append(dict(type="set_perfusion",value=round(target,2)))
    if policy=="feedback":
        return out
    invalid=latest(obs,"metabolic",valid=False)
    if invalid and not invalid["valid"] and not pending(obs,"metabolic") and not any(x.get("panel")=="metabolic" for x in out):
        out.append(dict(type="sample",panel="metabolic"))
    if m:
        nearest=min(obs["telemetry"],key=lambda x:abs(x["time_h"]-m["collected_h"]))
        if abs(nearest["ph"]-m["values"]["ph_independent"])>.12 and not pending(obs,"calibration"):
            c=latest(obs,"calibration")
            if not c or c["collected_h"]<m["collected_h"]:
                out.append(dict(type="sample",panel="calibration"))
        if m["values"]["glucose_g_l"]<3 and not pending(obs,"delivery"):
            d=latest(obs,"delivery")
            if not d or t-d["collected_h"]>=24:
                out.append(dict(type="sample",panel="delivery"))
    c=latest(obs,"calibration")
    corrected=any(e["title"]=="pH calibration corrected" for e in obs["events"])
    if c and abs(c["values"]["bias_estimate"])>.1 and t-c["collected_h"]<=12 and not corrected:
        out.append(dict(type="recalibrate"))
    d=latest(obs,"delivery")
    repaired=any(e["title"]=="Delivery path serviced" for e in obs["events"])
    if d and d["values"]["measured_ml_h"]<.8*d["values"]["command_ml_h"] and t-d["collected_h"]<=12 and not repaired:
        out.append(dict(type="repair_pump"))
    return out


def run(scenario,seed,policy,until=156,dt=.25):
    c=Campaign(scenario,seed,dt=dt)
    while c.clock<until:
        obs=c.observation()
        c.action(commands(obs,policy),advance_h=min(2,until-c.clock),
                 rationale=POLICIES[policy],actor=policy)
    return c

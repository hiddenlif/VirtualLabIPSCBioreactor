"""Units: hour, L, g, million cells. All operating histories are synthetic.

The fast pH/DO controller is numerical. Supervisors see observation() only.
The evaluator alone uses truth_summary(). No empirical calibration is claimed.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOP = json.loads((ROOT / "config/sop.json").read_text())
SCENARIOS = {
    "nominal": ("Routine expansion", "A reference campaign with biological variation."),
    "probe_drift": (
        "Instrument discrepancy",
        "Investigate agreement between independent measurements.",
    ),
    "delivery_loss": (
        "Delivery investigation",
        "Distinguish a commanded action from delivered flow.",
    ),
    "demand_shift": ("Metabolic change", "Investigate a change in culture demand."),
    "invalid_sample": (
        "Assay investigation",
        "Resolve an invalid measurement before making a quality claim.",
    ),
    "genomic_flag": (
        "Banking evidence",
        "Review stage-specific evidence independently of process appearance.",
    ),
    "combined": (
        "Overlapping disturbances",
        "A transfer challenge containing more than one disturbance.",
    ),
}
PANEL_TYPES = ("metabolic", "calibration", "delivery", "qc")


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def finite_number(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


class Campaign:
    def __init__(self, scenario="nominal", seed=17, label=None, dt=0.25):
        if scenario not in SCENARIOS:
            raise ValueError("Unknown scenario")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**31:
            raise ValueError("seed must be an integer in [0, 2147483647]")
        if dt <= 0 or dt > 0.5:
            raise ValueError("Integration step must be in (0, 0.5]")
        self.scenario, self.seed, self.dt = scenario, seed, dt
        self.label = label or f"EXP-{seed:04d}"
        r = random.Random(seed)
        self.mu = r.uniform(0.030, 0.038)
        self.qg = r.uniform(0.000026, 0.000034)
        self.onset = r.choice([34, 38, 42])
        self.clock = 0.0
        self.volume_l = 0.15
        self.cells = 75.0
        self.dead = 2.0
        self.glucose = 0.90  # g, initially 6 g/L
        self.lactate = 0.015
        self.ph, self.do = 7.05, 40.0
        self.flow = 3.0
        self.medium_ml, self.sample_ml = 0.0, 0.0
        self.sensor_corrected = self.pump_repaired = False
        self.invalid_emitted = False
        self.exposure_h = 0.0
        self.events, self.samples, self.telemetry, self.decisions = [], [], [], []
        self.balance = {
            "glucose_in": 0.0,
            "glucose_out": 0.0,
            "glucose_used": 0.0,
            "lactate_produced": 0.0,
            "lactate_out": 0.0,
            "cells_grown": 0.0,
            "cells_died": 0.0,
            "cells_sampled": 0.0,
            "dead_sampled": 0.0,
        }
        self.action_ids = {}
        self._event(
            "campaign",
            "Campaign inoculated",
            "Synthetic initial condition; 150 mL vessel.",
        )
        self._record()

    def _event(self, kind, title, detail, evidence=None):
        row = {
            "id": f"EV-{len(self.events) + 1:04d}",
            "time_h": round(self.clock, 6),
            "kind": kind,
            "title": title,
            "detail": detail,
        }
        if evidence:
            row["evidence"] = evidence
        self.events.append(row)
        return row["id"]

    def _faults(self, at=None):
        active = (self.clock if at is None else at) >= self.onset
        drift = (
            0.28
            if active
            and self.scenario in ("probe_drift", "combined")
            and not self.sensor_corrected
            else 0.0
        )
        delivery = (
            0.32
            if active
            and self.scenario in ("delivery_loss", "combined")
            and not self.pump_repaired
            else 1.0
        )
        demand = (
            2.1 if active and self.scenario in ("demand_shift", "combined") else 1.0
        )
        return drift, delivery, demand

    def _noise(self, key, scale, time=None):
        # Independent keyed streams preserve matched measurements across policies.
        s = f"{self.seed}:{key}:{self.clock if time is None else time:.6f}"
        return random.Random(
            int(hashlib.sha256(s.encode()).hexdigest()[:16], 16)
        ).gauss(0, scale)

    def _record(self):
        drift, _, _ = self._faults()
        self.telemetry.append(
            {
                "time_h": round(self.clock, 6),
                "ph": round(self.ph + drift + self._noise("online_ph", 0.008), 4),
                "do_pct": round(self.do + self._noise("online_do", 0.35), 3),
                "temperature_c": round(37 + self._noise("temp", 0.025), 3),
                "perfusion_command_ml_h": self.flow,
                "sensor_status": "calibration updated"
                if self.sensor_corrected
                else "scheduled calibration recorded",
                "evidence_layer": "simulated online measurement",
            }
        )

    def _tick(self, h):
        if self.clock >= SOP["process_end_h"]:
            self.clock += h
            return
        drift, delivery, demand = self._faults()
        delivered_l_h = self.flow * delivery / 1000
        if self.medium_ml + delivered_l_h * h * 1000 > SOP["limits"]["media_budget_ml"]:
            delivered_l_h = max(
                0, (SOP["limits"]["media_budget_ml"] - self.medium_ml) / 1000 / h
            )
        self.medium_ml += delivered_l_h * h * 1000
        g, l = self.glucose / self.volume_l, self.lactate / self.volume_l
        gin = delivered_l_h * 6.0 * h
        gout, lout = delivered_l_h * g * h, delivered_l_h * l * h
        demand_g = self.qg * self.cells * demand * h
        used = min(demand_g, max(0, self.glucose + gin - gout))
        produced = 1.6 * used
        self.glucose += gin - gout - used
        self.lactate += produced - lout
        self.balance["glucose_in"] += gin
        self.balance["glucose_out"] += gout
        self.balance["glucose_used"] += used
        self.balance["lactate_produced"] += produced
        self.balance["lactate_out"] += lout
        # Numerical fast control; biased online pH changes the real controlled state.
        ph_target = 7.05 - drift - 0.025 * max(0, l - 1)
        self.ph += (ph_target - self.ph) * min(1, h / 1.5)
        do_target = max(5, 40 - max(0, self.cells * demand - 700) * 0.045)
        self.do += (do_target - self.do) * min(1, h / 1.0)
        exposure = (
            self.ph < SOP["history"]["ph_low"]
            or self.do < SOP["history"]["do_low_pct"]
            or g < 0.4
        )
        if exposure:
            self.exposure_h += h
        stress = (
            max(0, 0.6 - g) * 0.05
            + max(0, l - 2) * 0.002
            + max(0, 6.9 - self.ph) * 0.06
            + max(0, 20 - self.do) * 0.0005
        )
        lag = 0.25 if self.clock < 12 else 1
        growth_rate = (
            self.mu
            * lag
            * (g / (g + 0.35))
            / (1 + l / 4)
            * max(0.1, 1 - self.cells / 1800)
        )
        grown = max(0, growth_rate * self.cells * h)
        died = min(self.cells, (0.0006 + stress) * self.cells * h)
        self.cells += grown - died
        self.dead += died
        self.balance["cells_grown"] += grown
        self.balance["cells_died"] += died
        self.clock += h

    def advance(self, hours):
        hours = finite_number(hours, "hours")
        if hours <= 0 or hours > 48 or self.clock + hours > 168:
            raise ValueError("Advance 0 < hours <= 48, through hour 168 at most")
        target = self.clock + hours
        while self.clock < target - 1e-9:
            h = min(self.dt, target - self.clock)
            # Align every event boundary rather than applying a future fault early.
            for boundary in (
                self.onset,
                SOP["process_end_h"],
                *[s["result_h"] for s in self.samples if s["status"] == "pending"],
            ):
                if self.clock < boundary < self.clock + h:
                    h = boundary - self.clock
            self._tick(h)
            for s in self.samples:
                if s["status"] == "pending" and s["result_h"] <= self.clock + 1e-9:
                    s["status"] = "complete"
                    self._event(
                        "result",
                        f"{s['assay_label']} result available",
                        "Valid"
                        if s["valid"]
                        else "Invalid: sample integrity control failed",
                        [s["id"]],
                    )
            if self.clock <= 120 and (
                abs(self.clock - round(self.clock)) < 1e-8
                or abs(self.clock - target) < 1e-8
            ):
                self._record()
        return self.observation()

    def _add_sample(self, assay, label, delay, values, valid=True, volume=0.6):
        if self.clock >= SOP["process_end_h"]:
            raise ValueError("Collect samples before the process endpoint")
        if self.sample_ml + volume > SOP["limits"]["sample_budget_ml"] + 1e-9:
            raise ValueError("Sample volume budget exhausted")
        if self.medium_ml + volume > SOP["limits"]["media_budget_ml"] + 1e-9:
            raise ValueError("Insufficient medium for volume replacement")
        # Sample and fresh-medium replacement conserve fixed vessel volume.
        fraction = volume / (self.volume_l * 1000)
        cells_out, dead_out = self.cells * fraction, self.dead * fraction
        gout, lout = self.glucose * fraction, self.lactate * fraction
        gin = volume / 1000 * 6
        self.cells -= cells_out
        self.dead -= dead_out
        self.glucose += gin - gout
        self.lactate -= lout
        for k, v in (
            ("glucose_out", gout),
            ("glucose_in", gin),
            ("lactate_out", lout),
            ("cells_sampled", cells_out),
            ("dead_sampled", dead_out),
        ):
            self.balance[k] += v
        self.sample_ml += volume
        self.medium_ml += volume
        s = {
            "id": f"S-{len(self.samples) + 1:03d}",
            "batch": self.label,
            "assay": assay,
            "assay_label": label,
            "version": "1.0",
            "collected_h": round(self.clock, 6),
            "result_h": round(self.clock + delay, 6),
            "volume_ml": volume,
            "valid": valid,
            "status": "pending",
            "_values": values,
            "evidence_layer": "simulated sampled result",
        }
        self.samples.append(s)
        self._event(
            "sample",
            f"{label} collected",
            f"{volume:.1f} mL; result due at {s['result_h']:.0f} h",
            [s["id"]],
        )

    def collect(self, panel):
        if panel not in PANEL_TYPES:
            raise ValueError("Unknown measurement panel")
        if panel == "qc":
            if self.sample_ml + 1.5 > SOP["limits"]["sample_budget_ml"] + 1e-9:
                raise ValueError("Insufficient sample budget for QC panel")
            vals = self._qc_values()
            for assay, spec in SOP["evidence"].items():
                self._add_sample(
                    assay,
                    assay.replace("_", " ").title(),
                    spec["delay_h"],
                    {assay: vals[assay]},
                    volume=spec["volume_ml"],
                )
        elif panel == "metabolic":
            values = {
                "glucose_g_l": round(
                    max(
                        0, self.glucose / self.volume_l + self._noise("sample_g", 0.06)
                    ),
                    4,
                ),
                "lactate_g_l": round(
                    max(
                        0, self.lactate / self.volume_l + self._noise("sample_l", 0.04)
                    ),
                    4,
                ),
                "viable_cell_density_m_ml": round(
                    self.cells / (self.volume_l * 1000), 4
                ),
                "viability": round(self.cells / (self.cells + self.dead), 4),
                "ph_independent": round(self.ph + self._noise("sample_ph", 0.01), 4),
                "aggregate_diameter_um": round(100 * (self.cells / 75) ** (1 / 3), 1),
            }
            valid = not (
                self.scenario == "invalid_sample"
                and self.clock >= self.onset
                and not self.invalid_emitted
            )
            if not valid:
                values["lactate_g_l"] += 2
                self.invalid_emitted = True
            self._add_sample(panel, "Metabolic panel", 2, values, valid)
        elif panel == "calibration":
            drift, _, _ = self._faults()
            self._add_sample(
                panel,
                "Independent pH check",
                1,
                {
                    "ph_online": round(self.ph + drift, 4),
                    "ph_reference": round(self.ph, 4),
                    "bias_estimate": drift,
                },
                volume=0.3,
            )
        else:
            _, delivery, _ = self._faults()
            self._add_sample(
                panel,
                "Delivery verification",
                1,
                {
                    "command_ml_h": self.flow,
                    "measured_ml_h": round(self.flow * delivery, 4),
                },
                volume=0.1,
            )

    def _qc_values(self):
        return {
            "identity": "match",
            "phenotype": round(max(0.6, 0.96 - self.exposure_h * 0.001), 4),
            "viability": round(self.cells / (self.cells + self.dead), 4),
            "genomic_screen": "flag" if self.scenario == "genomic_flag" else "no_flag",
            "microbial_screen": "negative",
        }

    def _latest(self, assay, valid_only=True):
        rows = [
            s
            for s in self.samples
            if s["assay"] == assay
            and s["status"] == "complete"
            and (s["valid"] or not valid_only)
        ]
        return max(rows, key=lambda s: (s["collected_h"], s["id"])) if rows else None

    def action(
        self,
        commands=None,
        advance_h=0,
        rationale="",
        evidence=None,
        action_id=None,
        actor="scientist",
    ):
        advance_h = finite_number(advance_h, "advance_h")
        if commands is not None and not isinstance(commands, list):
            raise ValueError("commands must be a list")
        request = {
            "commands": commands or [],
            "advance_h": advance_h,
            "rationale": rationale,
            "evidence": evidence or [],
            "actor": actor,
        }
        if action_id and action_id in self.action_ids:
            if self.action_ids[action_id] != digest(request):
                raise ValueError("Action ID already used for different content")
            return self.observation()
        if not isinstance(commands or [], list) or len(commands or []) > 8:
            raise ValueError("commands must contain at most eight actions")
        if not isinstance(rationale, str) or len(rationale) > 4000:
            raise ValueError("Rationale must be text of at most 4000 characters")
        known = {s["id"] for s in self.samples if s["status"] == "complete"} | {
            e["id"] for e in self.events
        }
        if not isinstance(evidence or [], list) or any(
            e not in known for e in evidence or []
        ):
            raise ValueError("Cite only available evidence IDs")
        before = self.observation()
        # Transactional draft prevents partial mutations when any command is invalid.
        draft = copy.deepcopy(self)
        for command in commands or []:
            if not isinstance(command, dict):
                # Invalid actions share the public ValueError validation contract.
                raise ValueError("Each command must be an object")  # noqa: TRY004
            kind = command.get("type")
            if kind == "set_perfusion":
                value = finite_number(command.get("value"), "perfusion")
                if not 0 <= value <= 12 or draft.clock >= 120:
                    raise ValueError("Perfusion must be 0–12 mL/h during culture")
                draft.flow = value
                draft._event(
                    "control",
                    "Perfusion command updated",
                    f"{value:g} mL/h; delivery requires independent verification",
                )
            elif kind == "sample":
                draft.collect(command.get("panel"))
            elif kind == "recalibrate":
                check = draft._latest("calibration")
                if not check or draft.clock - check["collected_h"] > 12:
                    raise ValueError(
                        "Recalibration needs a valid independent check from the last 12 h"
                    )
                draft.sensor_corrected = True
                draft._event(
                    "intervention",
                    "pH calibration corrected",
                    "Earlier history is retained.",
                    [check["id"]],
                )
            elif kind == "repair_pump":
                check = draft._latest("delivery")
                if not check or draft.clock - check["collected_h"] > 12:
                    raise ValueError(
                        "Pump service needs a delivery check from the last 12 h"
                    )
                draft.pump_repaired = True
                draft._event(
                    "intervention",
                    "Delivery path serviced",
                    "Subsequent delivery should be verified.",
                    [check["id"]],
                )
            elif kind == "recommend":
                if command.get("value") not in ("accept", "hold", "reject"):
                    raise ValueError("Disposition must be accept, hold, or reject")
                draft._event(
                    "recommendation",
                    f"{actor}: {command['value'].upper()}",
                    rationale,
                    evidence,
                )
            else:
                raise ValueError("Unsupported action")
        if advance_h:
            draft.advance(advance_h)
        draft.decisions.append(
            {
                "id": f"D-{len(draft.decisions) + 1:03d}",
                "time_h": before["time_h"],
                "actor": actor,
                "observation_sha256": digest(before),
                "request": request,
                "available_evidence_ids": sorted(known),
            }
        )
        if action_id:
            draft.action_ids[action_id] = digest(request)
        self.__dict__.update(draft.__dict__)
        return self.observation()

    def observation(self):
        # Fresh public objects prevent callers from mutating simulator state.
        results = []
        for s in self.samples:
            public = {
                k: copy.deepcopy(v)
                for k, v in s.items()
                if not k.startswith("_") and k != "valid"
            }
            if s["status"] == "complete":
                public.update(values=copy.deepcopy(s["_values"]), valid=s["valid"])
            results.append(public)
        return {
            "batch": self.label,
            "time_h": round(self.clock, 6),
            "process_end_h": 120,
            "sop": f"{SOP['id']} v{SOP['version']}",
            "evidence_layer": "synthetic research simulation",
            "telemetry": copy.deepcopy(self.telemetry),
            "samples": results,
            "events": copy.deepcopy(self.events),
            "decisions": copy.deepcopy(self.decisions),
            "resources": {
                "medium_used_ml": round(self.medium_ml, 3),
                "medium_remaining_ml": round(2000 - self.medium_ml, 3),
                "sample_used_ml": round(self.sample_ml, 3),
                "sample_remaining_ml": round(18 - self.sample_ml, 3),
            },
            "settings": {"perfusion_ml_h": self.flow, "volume_ml": 150},
            "assessment": self.assessment(),
        }

    def assessment(self):
        pending, failures, evidence_ids = [], [], []
        for assay, spec in SOP["evidence"].items():
            rows = [
                s
                for s in self.samples
                if s["assay"] == assay
                and s["batch"] == self.label
                and s["version"] == "1.0"
                and s["collected_h"] >= SOP["qc_checkpoint_h"]
                and s["status"] == "complete"
                and s["valid"]
            ]
            if not rows:
                pending.append(assay)
                continue
            # A subsequent passing result cannot erase a valid failing result.
            for s in rows:
                value = s["_values"][assay]
                if ("pass" in spec and value != spec["pass"]) or (
                    "min" in spec and value < spec["min"]
                ):
                    failures.append(f"{assay}: valid failing result {s['id']}")
                evidence_ids.append(s["id"])
        issues = []
        if any(
            r["ph"] < 6.8 or r["do_pct"] < 20
            for r in self.telemetry
            if r["time_h"] <= 120
        ):
            issues.append("Online process excursion requires investigation")
        for s in self.samples:
            if s["status"] != "complete" or not s["valid"]:
                continue
            v = s["_values"]
            if s["assay"] == "metabolic" and (
                v["ph_independent"] < 6.8 or v["glucose_g_l"] < 0.4
            ):
                issues.append(
                    f"Adverse sampled process condition at {s['collected_h']:g} h ({s['id']})"
                )
            if s["assay"] == "calibration" and abs(v["bias_estimate"]) > 0.1:
                issues.append(f"Historical sensor discrepancy needs review ({s['id']})")
        issues = list(dict.fromkeys(issues))
        if failures:
            decision = "reject"
        elif pending or issues or self.clock < 120:
            decision = "hold"
        else:
            decision = "accept"
        reasons = (
            failures
            + issues
            + (["Process not complete"] if self.clock < 120 else [])
            + (
                ["Missing qualifying evidence: " + ", ".join(pending)]
                if pending
                else []
            )
        )
        return {
            "decision": decision,
            "reasons": reasons
            or ["Complete passing evidence under the simulation SOP"],
            "evidence_ids": sorted(set(evidence_ids)),
            "missing": pending,
            "history_issues": issues,
            "scope": "Simulated banking recommendation only",
        }

    def truth_summary(self):
        """Evaluator-only latent endpoints; never serialized by the public API."""
        true = self._qc_values()
        fail = any(
            ("pass" in spec and true[a] != spec["pass"])
            or ("min" in spec and true[a] < spec["min"])
            for a, spec in SOP["evidence"].items()
        )
        latent = "reject" if fail else "hold" if self.exposure_h > 4 else "accept"
        return {
            "scenario": self.scenario,
            "seed": self.seed,
            "onset_h": self.onset,
            "mu_h": self.mu,
            "qg": self.qg,
            "yield_million_cells": self.cells,
            "viability": self.cells / (self.cells + self.dead),
            "adverse_exposure_h": self.exposure_h,
            "medium_used_ml": self.medium_ml,
            "sample_used_ml": self.sample_ml,
            "latent_quality_decision": latent,
            "public_decision": self.assessment()["decision"],
            "balances": self.balance_residuals(),
        }

    def balance_residuals(self):
        b = self.balance
        return {
            "glucose_g": self.glucose
            - (0.9 + b["glucose_in"] - b["glucose_out"] - b["glucose_used"]),
            "lactate_g": self.lactate
            - (0.015 + b["lactate_produced"] - b["lactate_out"]),
            "viable_million": self.cells
            - (75 + b["cells_grown"] - b["cells_died"] - b["cells_sampled"]),
            "dead_million": self.dead - (2 + b["cells_died"] - b["dead_sampled"]),
        }

    def dossier(self):
        obs = self.observation()
        return {
            "schema_version": "1.0",
            "provenance": "All campaign values and QC results are simulated",
            "sop": copy.deepcopy(SOP),
            "campaign": obs,
            "observation_sha256": digest(obs),
            "conclusion": obs["assessment"],
            "limitations": [
                "Not calibrated to raw process data",
                "No real batch release or functional pluripotency claim",
                "Rule-based supervisors are not LLMs",
            ],
        }

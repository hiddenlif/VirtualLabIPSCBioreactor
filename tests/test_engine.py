import copy
import json
import unittest

from ipsc_lab.engine import Campaign, digest
from ipsc_lab.policies import run


class SimulationTests(unittest.TestCase):
    def test_mass_and_cell_accounting_across_sampling_and_faults(self):
        for scenario in (
            "nominal",
            "probe_drift",
            "delivery_loss",
            "demand_shift",
            "combined",
        ):
            c = run(scenario, 17, "diagnostic")
            for value in c.balance_residuals().values():
                self.assertLess(abs(value), 1e-8)
            self.assertGreaterEqual(c.glucose, 0)
            self.assertGreaterEqual(c.cells, 0)
            self.assertLessEqual(c.medium_ml, 2000 + 1e-7)
            self.assertLessEqual(c.sample_ml, 18 + 1e-7)

    def test_passive_observation_and_public_boundary(self):
        c = Campaign("genomic_flag")
        before = copy.deepcopy(c.__dict__)
        obs = c.observation()
        self.assertEqual(before, c.__dict__)
        self.assertFalse(
            any(
                k in json.dumps(obs)
                for k in (
                    "latent_quality_decision",
                    "genomic_flag",
                    "onset_h",
                    "_values",
                )
            )
        )
        obs["telemetry"][0]["ph"] = 99
        self.assertNotEqual(c.telemetry[0]["ph"], 99)
        c.action([{"type": "sample", "panel": "qc"}])
        self.assertNotIn("values", c.observation()["samples"][0])

    def test_reproducibility_and_time_step_convergence(self):
        a = run("combined", 29, "feedback")
        b = run("combined", 29, "feedback")
        self.assertEqual(digest(a.dossier()), digest(b.dossier()))
        # An independent refined discretization checks numerical sensitivity.
        for scenario in ("nominal", "demand_shift", "combined"):
            x = run(scenario, 43, "fixed", dt=0.25)
            y = run(scenario, 43, "fixed", dt=0.125)
            self.assertLess(abs(x.cells - y.cells) / y.cells, 0.015)
            self.assertLess(abs(x.glucose - y.glucose), 0.01)

    def test_invalid_actions_are_atomic(self):
        c = Campaign()
        before = digest(c.__dict__)
        with self.assertRaises(ValueError):
            c.action([{"type": "set_perfusion", "value": 8}, {"type": "repair_pump"}])
        self.assertEqual(before, digest(c.__dict__))
        for value in (float("nan"), float("inf"), True, "8", -1, 13):
            with self.assertRaises(ValueError):
                c.action([{"type": "set_perfusion", "value": value}])

    def test_idempotence_and_counterfactual_branch(self):
        c = Campaign()
        c.action([{"type": "sample", "panel": "metabolic"}], action_id="once")
        before = digest(c.__dict__)
        c.action([{"type": "sample", "panel": "metabolic"}], action_id="once")
        self.assertEqual(before, digest(c.__dict__))
        with self.assertRaises(ValueError):
            c.action([], advance_h=2, action_id="once")
        branch = copy.deepcopy(c)
        branch.action([{"type": "set_perfusion", "value": 12}], advance_h=24)
        self.assertEqual(c.clock, 0)
        self.assertNotEqual(c.glucose, branch.glucose)

    def test_result_collection_and_result_time_are_distinct(self):
        c = Campaign()
        c.collect("metabolic")
        c.advance(1)
        self.assertEqual(c.observation()["samples"][0]["status"], "pending")
        c.advance(1)
        self.assertEqual(c.observation()["samples"][0]["status"], "complete")
        self.assertEqual(c.samples[0]["collected_h"], 0)
        self.assertEqual(c.samples[0]["result_h"], 2)

    def test_stale_and_invalid_evidence_cannot_release(self):
        c = Campaign()
        c.collect("qc")
        c.advance(48)
        c.advance(48)
        c.advance(48)
        self.assertEqual(c.assessment()["decision"], "hold")
        c = run("nominal", 17, "diagnostic")
        self.assertEqual(c.assessment()["decision"], "accept")
        qualifying = next(s for s in c.samples if s["assay"] == "identity")
        qualifying["valid"] = False
        self.assertEqual(c.assessment()["decision"], "hold")
        qualifying["valid"] = True
        qualifying["batch"] = "other"
        self.assertEqual(c.assessment()["decision"], "hold")

    def test_valid_failure_and_history_survive_normal_endpoint(self):
        c = run("genomic_flag", 17, "diagnostic")
        self.assertEqual(c.assessment()["decision"], "reject")
        sample = next(s for s in c.samples if s["assay"] == "genomic_screen")
        newer = copy.deepcopy(sample)
        newer["id"] = "S-999"
        newer["collected_h"] = 110
        newer["_values"] = {"genomic_screen": "no_flag"}
        c.samples.append(newer)
        self.assertEqual(c.assessment()["decision"], "reject")
        c = run("probe_drift", 17, "diagnostic")
        self.assertTrue(any(e["title"] == "pH calibration corrected" for e in c.events))
        self.assertTrue(c.assessment()["history_issues"])
        self.assertEqual(c.assessment()["decision"], "hold")

    def test_faults_have_consequences_and_independent_checks(self):
        c = Campaign("delivery_loss", 17)
        c.advance(48)
        c.collect("delivery")
        c.advance(1)
        v = c.observation()["samples"][-1]["values"]
        self.assertLess(v["measured_ml_h"], 0.5 * v["command_ml_h"])
        c.action([{"type": "repair_pump"}])
        c.collect("delivery")
        c.advance(1)
        v = c.observation()["samples"][-1]["values"]
        self.assertAlmostEqual(v["measured_ml_h"], v["command_ml_h"])
        c = Campaign("probe_drift", 17)
        c.advance(48)
        c.collect("calibration")
        c.advance(1)
        self.assertAlmostEqual(
            c.observation()["samples"][-1]["values"]["bias_estimate"], 0.28
        )
        a = run("nominal", 17, "fixed")
        b = run("demand_shift", 17, "fixed")
        self.assertGreater(abs(a.cells - b.cells), 10)


if __name__ == "__main__":
    unittest.main()

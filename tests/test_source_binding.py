"""Maintenance must not silently admit unrecorded scientific source changes."""

import json
import unittest
from unittest.mock import patch

from scripts import evaluate


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        plan = evaluate.ROOT / "reports/comparison-v1/PLAN.json"
        self.baseline = json.loads(plan.read_text())["source_hashes"]

    def test_recorded_cleanup_revision_is_accepted(self):
        self.assertEqual(
            evaluate.verify_source_binding(self.baseline), "ruff-cleanup-v1"
        )

    def test_unrecorded_source_edit_is_rejected(self):
        changed = evaluate.source_hashes()
        changed["ipsc_lab/engine.py"] = "0" * 64
        with (
            patch.object(evaluate, "source_hashes", return_value=changed),
            self.assertRaises(ValueError),
        ):
            evaluate.verify_source_binding(self.baseline)

    def test_unrelated_original_study_is_rejected(self):
        self.baseline["ipsc_lab/engine.py"] = "0" * 64
        with self.assertRaises(ValueError):
            evaluate.verify_source_binding(self.baseline)

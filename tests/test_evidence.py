import unittest
from unittest.mock import patch
import auth
from demo_evidence import run_evidence, synthetic_events


class EvidenceTests(unittest.TestCase):
    def test_deterministic_generator_has_valid_events(self):
        self.assertEqual(synthetic_events(8), synthetic_events(8))
        self.assertNotEqual(synthetic_events(8), synthetic_events(9))
        self.assertIsNotNone(auth.extract_features(synthetic_events(8)))

    def test_holdout_and_report_boundaries(self):
        report = run_evidence()
        self.assertTrue(report["passed"])
        split = report["split"]
        groups = [set(v) for v in split.values()]
        for i in range(len(groups)):
            for j in range(i):
                self.assertFalse(groups[i] & groups[j])
        self.assertEqual(report["heldout_same_generator"]["total"], 20)
        self.assertEqual(report["heldout_shifted_generator"]["total"], 20)
        self.assertLessEqual(report["synthetic_covariance_rank"], 21)

    def test_report_detects_nonfinite_validation_regression(self):
        extract = auth.extract_features

        def broken(events):
            if events and events[0]["timestamp"] != events[0]["timestamp"]:
                return extract(synthetic_events(0))
            return extract(events)

        with patch.object(auth, "extract_features", broken):
            report = run_evidence()
        self.assertFalse(report["passed"])
        case = next(c for c in report["cases"] if c["scenario"] == "nonfinite_time_rejected")
        self.assertFalse(case["passed"])

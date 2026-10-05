import unittest
import numpy as np
from auth import TARGET, extract_features


class FeatureRegressionTests(unittest.TestCase):
    def events(self):
        return [event for i, key in enumerate(TARGET) for event in (
            {"key": key, "timestamp": i * 100, "action": "down"},
            {"key": key, "timestamp": i * 100 + 40, "action": "up"},
        )]

    def test_repeated_letters_keep_nonzero_dwell(self):
        features = extract_features(self.events())
        self.assertEqual(features.shape, (31,))
        np.testing.assert_allclose(features[:11], 40)
        np.testing.assert_allclose(features[11:21], 100)
        np.testing.assert_allclose(features[21:], 60)

    def test_incomplete_input_is_rejected(self):
        self.assertIsNone(extract_features(self.events()[:-1]))

    def test_wrong_character_counts_are_rejected(self):
        events = self.events()
        for event in events:
            if event["key"] == "l":
                event["key"] = "x"
        self.assertIsNone(extract_features(events))


if __name__ == '__main__':
    unittest.main()

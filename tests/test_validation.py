"""Synthetic malformed-event cases and normal key-rollover behavior."""
import copy
import unittest

import numpy as np

from auth import TARGET, extract_features, validate_user_id, InputError


def events(text=TARGET):
    return [event for i, key in enumerate(text) for event in (
        {'key':key, 'action':'down', 'timestamp':i*100},
        {'key':key, 'action':'up', 'timestamp':i*100+40})]


class ValidationTests(unittest.TestCase):
    def test_wrong_order_with_same_character_counts_is_rejected(self):
        self.assertIsNone(extract_features(events(TARGET[::-1])))

    def test_same_time_release_is_rejected(self):
        data = events(); data[1]['timestamp'] = data[0]['timestamp']
        self.assertIsNone(extract_features(data))

    def test_release_before_press_is_rejected(self):
        data = events(); data[1]['timestamp'] = -1
        self.assertIsNone(extract_features(data))

    def test_out_of_order_event_times_are_rejected(self):
        data = events(); data[4]['timestamp'] = 30
        self.assertIsNone(extract_features(data))

    def test_non_numeric_nonfinite_and_huge_times_are_rejected(self):
        for value in ['10', None, True, [], {}, float('nan'), float('inf'), -1, 10**400]:
            with self.subTest(value=repr(value)):
                data = events(); data[0]['timestamp'] = value
                self.assertIsNone(extract_features(data))

    def test_bad_event_shapes_are_rejected(self):
        for value in [None, {}, 'hello', [None]*22, events()+events(), events()[:-1]]:
            with self.subTest(type=type(value).__name__):
                self.assertIsNone(extract_features(value))
        for field,value in [('action','press'),('key',None),('key',[]),('extra',True)]:
            data = events(); data[0][field] = value
            self.assertIsNone(extract_features(data))
        data = events(); del data[0]['action']
        self.assertIsNone(extract_features(data))

    def test_unmatched_and_duplicate_releases_are_rejected(self):
        data = events(); data[1]['key'] = 'e'
        self.assertIsNone(extract_features(data))
        data = events(); data[2] = copy.deepcopy(data[1]); data[2]['timestamp'] = 100
        self.assertIsNone(extract_features(data))

    def test_rollover_pairs_releases_by_press_not_release_order(self):
        data = events()
        data[1]['timestamp'] = 180  # h stays down after e is pressed and released.
        data = sorted(data, key=lambda event:event['timestamp'])
        features = extract_features(data)
        self.assertIsNotNone(features)
        self.assertEqual(features[0],180)
        self.assertEqual(features[1],40)
        self.assertEqual(features[21],-80)
        self.assertTrue(np.isfinite(features).all())

    def test_repeat_key_before_release_is_rejected(self):
        data = events(); data[5]['timestamp'] = 340  # First l remains held at second l press.
        data = sorted(data,key=lambda event:event['timestamp'])
        self.assertIsNone(extract_features(data))

    def test_reserved_names_and_path_syntax_are_rejected(self):
        for uid in ['../escape','..',r'a\b','a/b','a.b','A:drive','a\x00b','NUL','con','COM1','x'*65,' userA',None,[],True]:
            with self.subTest(uid=repr(uid)), self.assertRaises(InputError):
                validate_user_id(uid)
        self.assertEqual(validate_user_id('userA-42_ok'),'userA-42_ok')


if __name__=='__main__':unittest.main()

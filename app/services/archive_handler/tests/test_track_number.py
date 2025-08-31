import unittest

from ..utils import get_track_number


class TestReceivingTrackNumber(unittest.TestCase):
    def test_regular_number(self):
        input_str = [
            "0",
            "01",
            "012",
        ]

        expected_resd = [
            0,
            1,
            12,
        ]

        for i, raw in enumerate(input_str):
            num = get_track_number(raw)
            self.assertEqual(num, expected_resd[i])

    def test_non_digit_string(self):
        input_str = [
            None,
            "",
            "abcde",
            "1/1",
            "0123/1",
            "1abc32def4",
            "abc32def4",
        ]

        expected_res = [
            -1,
            -1,
            -1,
            1,
            123,
            1,
            32,
        ]

        for i, raw in enumerate(input_str):
            num = get_track_number(raw)
            self.assertEqual(num, expected_res[i], f"{i}: {num}!={expected_res[i]}")

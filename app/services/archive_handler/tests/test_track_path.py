from os import path
import unittest


class TestGetTrackTitleFromPath(unittest.TestCase):
    def test(self):
        input_str = [
            "1.mp3",
            "_1/2.mp3",
            "/1/2/3.mp3",
        ]

        expected_resd = [
            "1.mp3",
            "2.mp3",
            "3.mp3",
        ]

        for i, raw in enumerate(input_str):
            num = __get_track_title_from_path(raw)
            self.assertEqual(num, expected_resd[i])


def __get_track_title_from_path(raw: str) -> str:
    return path.basename(path.normpath(raw))
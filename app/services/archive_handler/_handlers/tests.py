import unittest
from typing import List


class ListingTest(unittest.TestCase):
    def test_list(self):
        path = "/2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)"
        expected = [
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/03 - A Nearly Peaceful )Place.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/01 - In Temeria (Intro).mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/09 - An Army Lying in Wait.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/02 - Assassins of Kings.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/29 - The Lone Survivor.mp3",
        ]

        input_strings = [
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/test/03-test.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/03 - A Nearly Peaceful )Place.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/01 - In Temeria (Intro).mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/09 - An Army Lying in Wait.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/02 - Assassins of Kings.mp3",
            "2012 - The Witcher 2 - Assassins of Kings Enhanced Edition Official Soundtrack (Adam Skorupa & Krzysztof Wierzynkiewicz)/29 - The Lone Survivor.mp3",
        ]

        result = get_files(path, input_strings)
        self.assertEqual(expected, result)


def get_files(path: str, input_st: List[str]) -> List[str]:
    p = path.lstrip("/")
    return [
        name for name in input_st
        if name.startswith(p)
        and "/" not in name[len(p)+1:]
        and not name.endswith("/")
    ]

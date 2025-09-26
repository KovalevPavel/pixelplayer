import re
from typing import Union

from ...decoding.decoding import get_audio_params
from ..base_meta_parser import BaseMetaParser
from ..metadata import TrackMetaData


class MP3Parser(BaseMetaParser):
    def get_metadata(self, name: str) -> TrackMetaData:

        data = get_audio_params(name)
        tags: dict = data["tags"]

        return TrackMetaData(
            track_title=tags["track_title"],
            track_number=self.__get_track_number(raw=tags["track_number"]),
            album=tags["album"],
            artist=tags["artist"],
            genre=tags["genre"],
            mime=tags["mime"],
        )

    def __get_track_number(self, raw: Union[str, None]) -> str:
        if not raw:
            return str(-1)

        segments = re.findall(r"\d+", raw)

        return str(segments[0]) if len(segments) > 0 else str(-1)


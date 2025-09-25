from ..base_meta_parser import BaseMetaParser
from ..metadata import TrackMetaData


class MP3Parser(BaseMetaParser):
    def get_metadata(self) -> TrackMetaData:
        return TrackMetaData(
            track_title=self.file.tags.get("TIT2", [None])[0] if self.file else None,
            track_number=self.file.tags.get("TRCK", [None])[0] if self.file else None,
            album=self.file.tags.get("TALB", [None])[0] if self.file else None,
            artist=self.file.tags.get("TPE1", [None])[0] if self.file else None,
            genre=None,
        )

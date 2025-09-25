from app.services.meta_parser.base_meta_parser import BaseMetaParser
from app.services.meta_parser.metadata import TrackMetaData


class FLACParser(BaseMetaParser):
    def get_metadata(self) -> TrackMetaData:
        return TrackMetaData(
            track_title=self.file.get("title", [None])[0],
            track_number=self.file.get("tracknumber", [None])[0],
            artist=self.file.get("artist", [None])[0],
            album=self.file.get("album", [None])[0],
            genre=None,
        )

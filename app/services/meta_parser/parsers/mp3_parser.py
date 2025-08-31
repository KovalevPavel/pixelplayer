import logging
from typing import Optional

from mutagen.id3 import ID3

from ..base_meta_parser import BaseMetaParser
from ..metadata import CoverMetaData, TrackMetaData
from ..utils import cover_info


class MP3Parser(BaseMetaParser):
    def get_metadata(self) -> TrackMetaData:
        return TrackMetaData(
            track_title=self.file.tags.get("TIT2", [None])[0] if self.file else None,
            track_number=self.file.tags.get("TRCK", [None])[0] if self.file else None,
            album=self.file.tags.get("TALB", [None])[0] if self.file else None,
            artist=self.file.tags.get("TPE1", [None])[0] if self.file else None,
            genre=None,
        )

    def extract_cover(self) -> Optional[CoverMetaData]:
        id3 = ID3(fileobj=self.fileobj)
        logging.warning(f"fileobj: {self.fileobj}, id3: {id3}")
        apic_tags = id3.getall("APIC")
        if apic_tags:
            return cover_info(apic_tags[0].data, apic_tags[0].mime)
        return None

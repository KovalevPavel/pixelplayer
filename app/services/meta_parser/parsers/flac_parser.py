import base64
import binascii
from itertools import zip_longest
from typing import Optional

import mutagen
import mutagen.flac as mflac

from app.services.meta_parser.base_meta_parser import BaseMetaParser
from app.services.meta_parser.metadata import CoverMetaData, TrackMetaData
from app.services.meta_parser.utils import cover_info, detect_mime_from_bytes


class FLACParser(BaseMetaParser):
    def get_metadata(self) -> TrackMetaData:
        return TrackMetaData(
            track_title=self.file.get("title", [None])[0],
            track_number=self.file.get("tracknumber", [None])[0],
            artist=self.file.get("artist", [None])[0],
            album=self.file.get("album", [None])[0],
            genre=None,
        )

    def extract_cover(self) -> Optional[CoverMetaData]:
        tags = self.file.tags
        # 1. Пробуем metadata_block_picture
        b64_list = tags.get("metadata_block_picture", [])
        for b64_data in b64_list:
            try:
                data = base64.b64decode(b64_data)
                pic = mflac.Picture(data)
                raw = pic.data
                if isinstance(raw, str):
                    raw = raw.encode("latin-1")
                return cover_info(raw, pic.mime)
            except (binascii.Error, mutagen.MutagenError):
                continue

        # 2. fallback: coverart + coverartmime
        vals = tags.get("coverart", [])
        mimes = tags.get("coverartmime", [])
        for val, mime in zip_longest(vals, mimes, fillvalue=None):
            try:
                data = base64.b64decode(val.encode("ascii"))
            except (TypeError, ValueError):
                continue
            ctype = mime or detect_mime_from_bytes(data)
            return cover_info(data, ctype)

        return None

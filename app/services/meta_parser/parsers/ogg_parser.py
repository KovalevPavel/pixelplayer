import base64
import binascii
from itertools import zip_longest
from typing import Optional

import mutagen
import mutagen.flac as mflac

from app.services.meta_parser.base_meta_parser import BaseMetaParser
from app.services.meta_parser.metadata import CoverMetaData, TrackMetaData
from app.services.meta_parser.utils import cover_info, detect_mime_from_bytes


def _ensure_bytes(data) -> bytes:
    """
    Некоторые поля могут внезапно оказаться str — аккуратно приводим к bytes.
    """
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    # Vorbis-комментарии — текстовые; если вдруг пришло str с бинарником,
    # безопаснее всего интерпретировать как latin-1 (без потерь по байтам).
    return str(data).encode("latin-1")


class OggParser(BaseMetaParser):
    def get_metadata(self) -> TrackMetaData:
        return TrackMetaData(
            track_title=self.file.get("title", [None])[0],
            artist=self.file.get("artist", [None])[0],
            album=self.file.get("album", [None])[0],
            track_number=self.file.get("tracknumber", [None])[0],
            genre=None,
        )

    def extract_cover(self) -> Optional[CoverMetaData]:
        tags = getattr(self.file, "tags", {}) or {}

        # 1) metadata_block_picture (рекомендуется документацией Mutagen)
        for b64_data in tags.get("metadata_block_picture", []):
            try:
                blob = base64.b64decode(_ensure_bytes(b64_data))
                # mflac.Picture умеет парсить бинарную структуру FLAC Picture
                pic = mflac.Picture(blob)
                raw = _ensure_bytes(pic.data)  # защита от "bytes expected, but got str"
                return cover_info(raw, getattr(pic, "mime", None))
            except (ValueError, binascii.Error, mutagen.MutagenError):
                # некорректная base64/структура — пробуем следующий вариант
                continue

        # 2) fallback: coverart (base64) + coverartmime
        vals = tags.get("coverart", [])
        mimes = tags.get("coverartmime", [])
        for b64_val, mime in zip_longest(vals, mimes, fillvalue=None):
            try:
                raw = base64.b64decode(_ensure_bytes(b64_val))
            except (TypeError, ValueError, binascii.Error):
                continue
            ctype = mime or detect_mime_from_bytes(raw)
            return cover_info(raw, ctype)

        return None

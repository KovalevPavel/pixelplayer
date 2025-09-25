from app.services.meta_parser.base_meta_parser import BaseMetaParser
from app.services.meta_parser.metadata import TrackMetaData


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

from io import BytesIO
from typing import Optional

import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from .base_meta_parser import BaseMetaParser
from .parsers.flac_parser import FLACParser
from .parsers.mp3_parser import MP3Parser
from .parsers.ogg_parser import OggParser


def get_parser(content_bytes: bytes) -> Optional[BaseMetaParser]:
    f = mutagen.File(BytesIO(content_bytes), easy=False)
    if isinstance(f, MP3):
        return MP3Parser(content_bytes)
    elif isinstance(f, FLAC):
        return FLACParser(content_bytes)
    elif isinstance(f, (OggVorbis, OggOpus)):
        return OggParser(content_bytes)
    else:
        return None

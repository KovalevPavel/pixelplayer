from io import BytesIO
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.mp3 import MP3

from ._parsers.mp3_parser import MP3Parser
from .base_meta_parser import BaseMetaParser

__mp3_parcer = MP3Parser()

def get_parser(file: str) -> Optional[BaseMetaParser]:
    content_bytes = Path(file).read_bytes()
    f = mutagen.File(BytesIO(content_bytes), easy=False)
    if isinstance(f, MP3):
        return __mp3_parcer
    else:
        return None

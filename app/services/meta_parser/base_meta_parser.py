from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional

import mutagen

from ..meta_parser.metadata import TrackMetaData
from .metadata import CoverMetaData


class BaseMetaParser(ABC):
    def __init__(self, content_bytes: bytes):
        self.content_bytes = bytes
        self.fileobj = BytesIO(content_bytes)
        self.file = mutagen.File(self.fileobj)

    @abstractmethod
    def get_metadata(self) -> TrackMetaData:
        pass

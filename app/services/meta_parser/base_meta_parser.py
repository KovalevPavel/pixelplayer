from abc import ABC, abstractmethod

from ..meta_parser.metadata import TrackMetaData


class BaseMetaParser(ABC):
    @abstractmethod
    def get_metadata(self, name: str) -> TrackMetaData:
        pass

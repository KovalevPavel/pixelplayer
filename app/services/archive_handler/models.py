from abc import ABC
from typing import List
from dataclasses import dataclass

from pydantic import BaseModel

from app.services.meta_parser.metadata import TrackMetaData, CoverMetaData

class ArchivedFile(ABC):
    id: str
    original_name: str
    content_bytes: bytes
    metadata: BaseModel


class AudioFileArchivedFile(ArchivedFile):
    """
    Модель для хранения данных аудиофайла

    Attributes
    ----------
    track_id: str
        id аудиофайла
    original_name: str
        имя аудиофайла
    track_bytes: bytes
        байты аудиофайла
    cover_id: str
        id обложки
    metadata: TrackMetaData
        метаданные аудиофайла
    """
    def __init__(self, track_id, original_name, track_bytes, cover_id, metadata: TrackMetaData):
        self.id = track_id
        self.original_name = original_name
        self.content_bytes = track_bytes
        self.cover_id = cover_id
        self.metadata = metadata


class CoverArchivedFile(ArchivedFile):
    """
    Модель для хранения данных обложки

    Attributes
    ----------
    cover_id: str
        id обложки
    original_name: str
        имя обложки
    cover_bytes: bytes
        байты обложки
    metadata: CoverMetaData
        метаданные обложки
    """
    def __init__(self, cover_id, original_name, cover_bytes, metadata: CoverMetaData):
        self.id = cover_id
        self.original_name = original_name
        self.bytes = cover_bytes
        self.metadata = metadata


@dataclass
class ExtractedData:
    """
    Модель для хранения данных извлеченных из архива
    Attributes
    ----------
    tracks: List[AudioFileArchivedFile]
        список аудиофайлов
    covers: List[CoverArchivedFile]
        список обложек
    """
    tracks: List[AudioFileArchivedFile]
    covers: List[CoverArchivedFile]

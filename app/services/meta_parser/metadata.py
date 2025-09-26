from typing import Optional

from pydantic import BaseModel


class TrackMetaData(BaseModel):
    """
    Модель для получения метаданных из файла
    """

    track_title: Optional[str]
    track_number: Optional[str]
    album: Optional[str]
    artist: Optional[str]
    genre: Optional[str]
    mime: Optional[str]


class CoverMetaData(BaseModel):
    """
    Модель для получения метаданных обложки
    """

    mime: Optional[str]
    width: Optional[int]
    heigth: Optional[int]
    format: Optional[str]
    bytes: bytes

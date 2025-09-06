from typing import Optional

from pydantic import BaseModel


class FileCreateDto(BaseModel):
    """
    DTO для создания файла при загрузке

    Attributes
    ----------
    id
        уникальный идентификатор файла
    original_name
        имя файла. Представляет собой строку вида <path>/<relative-to_root_on_device>/filename.ext
        Используется для визуализации дерева файлов на устройстве пользователя.
        Формируется исходя из иерархии файлов, которая загружается на сервер. Не имеет никакого отношения к
        структуре файлов в MinIO
    minio_object_name
        имя файла в MinIO. Представляет собой строку вида <MinIO_user>/file.ext
        Формируется при загрузке в MinIO и не имеет никакого отношения к иерархии файлов внутри архивов.
    size_bytes
        размер файла в байтах
    mime_type
        mime тип файла
    track_title
        название трека из метаданных файла
    track_number
        номер трека в альбоме. Если в метаданных не было поля, возвращается -1
    album
        название альбома
    artist
        имя артиста
    genre
        жанр
    """

    id: str
    original_name: str
    minio_object_name: str
    size_bytes: int
    mime_type: str

    track_title: Optional[str]
    track_number: int
    album: Optional[str]
    artist: Optional[str]
    genre: Optional[str]
    cover: Optional[str]


class FileDto(BaseModel):
    """
    Схема файла для ответа API при запросе списка файлов
    """

    id: str
    original_name: str
    size_bytes: int
    mime_type: str
    minio_object_name: str

    track_title: str
    track_number: int
    album: Optional[str]
    artist: Optional[str]
    genre: Optional[str]
    cover: Optional[str] = None

    class Config:
        from_attributes = True


class FileWithHierarchyDto(BaseModel):
    """
    Схема для ответа при запросе библиотеки пользователя
    """

    id: str
    original_name: str
    size_bytes: int
    mime_type: str
    minio_object_name: str

    class Config:
        from_attributes = True

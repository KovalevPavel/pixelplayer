from datetime import datetime

from pydantic import BaseModel


class FileCreateDto(BaseModel):
    """
    Схема для создания файла (внутреннее использование)
    """

    id: str
    original_name: str
    minio_object_name: str
    size_bytes: int
    mime_type: str


class FileDto(BaseModel):
    """
    Схема файла для ответа API при запросе списка файлов
    """

    id: str
    original_name: str
    size_bytes: int
    mime_type: str
    created_at: datetime
    owner_id: str
    minio_object_name: str

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

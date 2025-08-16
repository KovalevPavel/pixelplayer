from pydantic import BaseModel
from datetime import datetime
from typing import List

class FileCreateDto(BaseModel):
    """
    Схема для создания файла (внутреннее использование)
    """
    original_name: str
    minio_object_name: str
    size_bytes: int
    mime_type: str

class FileDto(BaseModel):
    """
    Схема файла для ответа API
    """
    id: str
    original_name: str
    size_bytes: int
    mime_type: str
    created_at: datetime
    owner_id: str
    is_dir: bool = False
    children: List[BaseModel] = []

    class Config:
        from_attributes = True

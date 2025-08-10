from pydantic import BaseModel
from datetime import datetime

# Схема для создания файла (внутреннее использование)
class FileCreate(BaseModel):
    original_name: str
    minio_object_name: str
    size_bytes: int
    mime_type: str

# Схема файла для ответа API
class File(BaseModel):
    id: int
    original_name: str
    size_bytes: int
    mime_type: str
    created_at: datetime
    owner_id: int

    class Config:
        orm_mode = True

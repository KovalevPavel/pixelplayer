from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.models.file_dto import FileWithHierarchyDto


class UserBaseDto(BaseModel):
    """
    Базовая схема для пользователя (для чтения из БД)
    """

    id: str
    username: str
    hashed_password: Optional[str] = None

    class Config:
        from_attributes = True  # Позволяет Pydantic работать с объектами SQLAlchemy


class UserDto(UserBaseDto):
    """
    Полная схема пользователя (для ответа API)
    """

    pass


class UserWithFilesDto(UserBaseDto):
    files: List[FileWithHierarchyDto]


class UserCreateDto(BaseModel):
    """
    Схема для создания пользователя (входные данные)
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

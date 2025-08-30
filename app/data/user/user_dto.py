from typing import List

from pydantic import BaseModel, Field

from ..file import file_dto


class UserBaseDto(BaseModel):
    """
    Базовая схема для пользователя (для чтения из БД)
    """

    id: str
    username: str

    class Config:
        from_attributes = True  # Позволяет Pydantic работать с объектами SQLAlchemy


class UserDto(UserBaseDto):
    """
    Полная схема пользователя (для ответа API)
    """

    pass


class UserWithFilesDto(UserBaseDto):
    files: List[file_dto.FileWithHierarchyDto]


class UserCreateDto(BaseModel):
    """
    Схема для создания пользователя (входные данные)
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

from typing import Optional

from pydantic import BaseModel, Field


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


class UserWithFilesDto(BaseModel):
    id: str
    username: str
    features: dict[str, bool]


class UserCreateDto(BaseModel):
    """
    Схема для создания пользователя (входные данные)
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

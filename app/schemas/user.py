from pydantic import BaseModel, Field

# Схема для создания пользователя (входные данные)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

# Базовая схема для пользователя (для чтения из БД)
class UserBase(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True # Позволяет Pydantic работать с объектами SQLAlchemy

# Полная схема пользователя (для ответа API)
class User(UserBase):
    pass

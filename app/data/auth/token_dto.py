from typing import Optional

from pydantic import BaseModel


class TokenDto(BaseModel):
    """
    Схема для ответа с токеном
    """

    access_token: str
    token_type: str


class TokenDataDto(BaseModel):
    """
    Схема для данных токена (содержимое JWT)
    """

    username: Optional[str] = None


class OAuth2PasswordRequestForm(BaseModel):
    """
    Специальная схема для получения данных из form-data, как требует стандарт OAuth2
    """

    username: str
    password: str

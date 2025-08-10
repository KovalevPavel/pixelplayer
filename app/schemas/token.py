from pydantic import BaseModel
from typing import Optional

# Схема для ответа с токеном
class Token(BaseModel):
    access_token: str
    token_type: str

# Схема для данных токена (содержимое JWT)
class TokenData(BaseModel):
    username: Optional[str] = None

# Специальная схема для получения данных из form-data, как требует стандарт OAuth2
class OAuth2PasswordRequestForm(BaseModel):
    username: str
    password: str

from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core import config

from ..core.models.user_dto import UserBaseDto
from ..db import user_repository

# Схема аутентификации OAuth2. 'tokenUrl' указывает на наш эндпоинт получения токена.
__oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/auth")


def get_current_active_user(token: str = Depends(__oauth2_scheme)):
    """
    Dependency для получения текущего пользователя из токена
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("user_id")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_repository.get_user_by_id(user_id=user_id)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создание access token'а
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def try_authenticate_user(username: str, password: str) -> UserBaseDto | None:
    """
    Авторизация пользователя
    """
    user = user_repository.get_user_by_username(username)
    if not user:
        return None
    if not user_repository.verify_password(password, user.hashed_password):
        return None
    return user

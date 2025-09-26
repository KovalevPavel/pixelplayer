from passlib.hash import argon2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from ..core.config import DATABASE_URL


def get_string_hash(string):
    """Хэширование пароля"""
    return argon2.hash(string)


# Создаем "движок" для подключения к БД
_engine = create_engine(DATABASE_URL)

# Базовый класс для всех наших моделей SQLAlchemy
Base = declarative_base()

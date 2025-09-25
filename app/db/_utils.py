from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from ..core.config import DATABASE_URL

# Контекст для хеширования паролей, используем bcrypt
__pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_string_hash(string):
    """Хэширование пароля"""
    return __pwd_context.hash(string)


# Создаем "движок" для подключения к БД
_engine = create_engine(DATABASE_URL)

# Базовый класс для всех наших моделей SQLAlchemy
Base = declarative_base()

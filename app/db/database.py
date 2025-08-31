import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..core.config import DATABASE_URL

# Базовый класс для всех наших моделей SQLAlchemy
Base = declarative_base()


def random_uuid():
    return str(uuid.uuid4())


# Создаем "движок" для подключения к БД
engine = create_engine(DATABASE_URL)

# Фабрика для создания сессий (транзакций) с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency для FastAPI: предоставляет сессию БД для каждого запроса
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

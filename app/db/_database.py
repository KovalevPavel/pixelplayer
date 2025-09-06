from sqlalchemy.orm import sessionmaker

from ._utils import _engine

# Фабрика для создания сессий (транзакций) с БД
__SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# Dependency для FastAPI: предоставляет сессию БД для каждого запроса
def get_db():
    db = __SessionLocal()
    try:
        yield db
    finally:
        db.close()

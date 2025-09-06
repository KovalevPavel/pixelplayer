from ._utils import Base, _engine


def init_database():
    """
    Создаем таблицы в БД на основе моделей SQLAlchemy
    В реальном продакшене для миграций лучше использовать Alembic
    """
    Base.metadata.create_all(bind=_engine)

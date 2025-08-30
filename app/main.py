from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from .api.api_files import fileRouter
from .api.api_user import authRouter
from .db.database import Base, engine

# Создаем таблицы в БД на основе моделей SQLAlchemy
# В реальном продакшене для миграций лучше использовать Alembic
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(
    title="File Storage Service",
    description="A service to store and manage files with user authentication.",
    version="1.0.0",
    root_path="/api",
)

# Подключаем роутеры с нашими эндпоинтами
app.include_router(authRouter, prefix="/v1", tags=["api_auth"])
app.include_router(fileRouter, prefix="/v1", tags=["api_files"])

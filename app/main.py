from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from .api.dirs import dirsRouter
from .db import models
from .db.database import engine
from .api.files import fileRouter
from .api.user import authRouter

# Создаем таблицы в БД на основе моделей SQLAlchemy
# В реальном продакшене для миграций лучше использовать Alembic
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(
    title="File Storage Service",
    description="A service to store and manage files with user authentication.",
    version="1.0.0",
    openapi_prefix="/api/v1"
)

# Подключаем роутеры с нашими эндпоинтами
app.include_router(authRouter, tags=["api_auth"])
app.include_router(fileRouter, tags=["api_files"])
app.include_router(dirsRouter, tags=["api_dirs"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the File Storage API. Go to /docs for API documentation."}

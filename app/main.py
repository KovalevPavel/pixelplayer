from fastapi import FastAPI
from .db import models
from .db.database import engine
from .api import routes

# Создаем таблицы в БД на основе моделей SQLAlchemy
# В реальном продакшене для миграций лучше использовать Alembic
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="File Storage Service",
    description="A service to store and manage files with user authentication.",
    version="1.0.0"
)

# Подключаем роутер с нашими эндпоинтами
app.include_router(routes.router, prefix="/api/v1", tags=["api"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the File Storage API. Go to /docs for API documentation."}

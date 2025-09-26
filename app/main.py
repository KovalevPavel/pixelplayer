from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from .api.api_files import fileRouter, internalRouter
from .api.api_user import authRouter
from .db.factory import init_database

init_database()

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
app.include_router(internalRouter, prefix="/v1", tags=["api_internal"])

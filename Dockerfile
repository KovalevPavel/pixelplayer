from python:3.11-slim

workdir /app

# Устанавливаем зависимости
copy ./requirements /app/requirements
run pip install --no-cache-dir --upgrade -r /app/requirements

# Копируем код приложения
copy ./app /app/app

# Запускаем приложение
# Uvicorn - это ASGI сервер для запуска FastAPI
cmd ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

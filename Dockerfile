FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости и FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \
    ffmpeg --version

# Устанавливаем Python зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Копируем код приложения
COPY ./app /app/app

# Запускаем приложение
# Uvicorn - это ASGI сервер для запуска FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

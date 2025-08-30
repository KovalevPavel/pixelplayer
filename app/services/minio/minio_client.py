import logging

from minio import Minio
from minio.error import S3Error
from ...core import config

minio_client = Minio(
    config.MINIO_ENDPOINT,
    access_key=config.MINIO_ACCESS_KEY,
    secret_key=config.MINIO_SECRET_KEY,
    # Мы внутри Docker-сети, можно использовать http
    secure=config.MINIO_USE_HTTPS,
)

# Создаем бакет, если он не существует
try:
    found = minio_client.bucket_exists(config.MINIO_BUCKET)
    if not found:
        minio_client.make_bucket(config.MINIO_BUCKET)
        logging.info(f"Bucket '{config.MINIO_BUCKET}' created.")
    else:
        logging.info(f"Bucket '{config.MINIO_BUCKET}' already exists.")
except S3Error as e:
    logging.error(f"Error connecting to MinIO: {e}")
    raise

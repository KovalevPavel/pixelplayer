from minio import Minio
from minio.error import S3Error
from ...core import config

minio_client = Minio(
    config.MINIO_ENDPOINT,
    access_key=config.MINIO_ACCESS_KEY,
    secret_key=config.MINIO_SECRET_KEY,
    secure=False # Внутри Docker-сети можно использовать http
)

# Создаем бакет, если он не существует
try:
    found = minio_client.bucket_exists(config.MINIO_BUCKET)
    if not found:
        minio_client.make_bucket(config.MINIO_BUCKET)
        print(f"Bucket '{config.MINIO_BUCKET}' created.")
    else:
        print(f"Bucket '{config.MINIO_BUCKET}' already exists.")
except S3Error as e:
    print(f"Error connecting to MinIO: {e}")
    raise

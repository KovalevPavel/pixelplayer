import logging

from minio import S3Error

from ...core import config
from .base_min_obj import BaseMinObj
from .minio_client import minio_client
from .offset_handler import BaseFileParams, Chunk, Full


def get_object(object_name: str, params: BaseFileParams):
    """
    Получение объекта
    """
    response = None
    stream = None

    match params:
        case Chunk():
            response = minio_client.get_object(
                config.MINIO_BUCKET,
                object_name,
                offset=params.first_byte,
                length=params.length,
            )
            stream = response.stream(params.length)
        case Full():
            response = minio_client.get_object(config.MINIO_BUCKET, object_name)
            stream = response.stream(params.file_length)

    response.close()
    return stream


def list_objects(user_prefix):
    """
    Перечисление объектов
    """
    return minio_client.list_objects(config.MINIO_BUCKET, prefix=user_prefix, recursive=True)


def put_object(file: BaseMinObj):
    """
    Сохранение объекта
    """
    try:
        minio_client.put_object(
            config.MINIO_BUCKET,
            object_name=file.object_name,
            data=file.data,
            length=file.length,
            content_type=file.content_type,
        )
    except S3Error as e:
        logging.error(f"Ошибка при загрузке файла: {e.code}: {e.message}")
        raise e
    finally:
        file.data.close()


def remove_object(object_name):
    """Удаление объекта из MinIO"""
    try:
        return minio_client.remove_object(config.MINIO_BUCKET, object_name)
    except S3Error as e:
        logging.error(f"Error while removing file: {e}")
        raise e


def remove_objects(objects):
    """Удаление нескольких объектов из MinIO"""
    try:
        return minio_client.remove_objects(config.MINIO_BUCKET, objects)
    except S3Error as e:
        logging.error(f"Error while removing file: {e}")
        raise e

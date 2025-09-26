import logging
from io import BytesIO
from typing import Optional

from fastapi import HTTPException
from minio import S3Error
from minio.deleteobjects import DeleteObject

from ..core import config
from ._minio_client import minio_client
from .minio_file import BaseMinObj
from .minio_file_params import BaseFileParams, Chunk, Full


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
    input_stream = BytesIO(file.data)
    try:
        minio_client.put_object(
            config.MINIO_BUCKET,
            object_name=file.object_name,
            data=input_stream,
            length=len(file.data),
            content_type=file.content_type,
        )
    except S3Error as e:
        logging.error(f"Ошибка при загрузке файла: {e.code}: {e.message}")
        raise e
    finally:
        input_stream.close()


def remove_object(object_name):
    """
    Удаление объекта из MinIO
    """
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


def remove_files_by_user(username: str) -> Optional[int]:
    # Проверяем, есть ли объекты с таким префиксом
    objects_to_delete = list(list_objects(user_prefix=username))

    if not objects_to_delete:
        return None

    try:
        errors_count = 0
        # Формируем генератор для удаления пачкой
        delete_objects = (DeleteObject(obj.object_name) for obj in objects_to_delete)
        errors = remove_objects(delete_objects)
        # Логируем ошибки
        for err in errors:
            errors_count += 1
            logging.error(f"Ошибка удаления файла {err.object_name}: {err}")

        return errors_count

    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении из MinIO: {err.message}")

from minio import S3Error

from .minio_client import minio_client
from .base_min_obj import BaseMinObj, MinFile, CHUNK_SIZE
from .offset_handler import BaseFileParams, Chunk, Full
from ...core import config

def get_object(object_name: str, params: BaseFileParams):
    response = None
    stream = None

    match params:
        case Chunk(first_byte, length):
            response = minio_client.get_object(config.MINIO_BUCKET, object_name, offset=first_byte, length=length)
            stream = response.stream(length)
        case Full(file_length):
            response = minio_client.get_object(config.MINIO_BUCKET, object_name)
            stream = response.stream(file_length)

    response.close()
    return stream

def list_objects(user_prefix):
    return minio_client.list_objects(config.MINIO_BUCKET, prefix=user_prefix, recursive=True)

def put_object(file: BaseMinObj):
    try:
        minio_client.put_object(
            config.MINIO_BUCKET,
            object_name=file.object_name,
            data=file.data,
            length=file.length,
            part_size=CHUNK_SIZE if isinstance(file, MinFile) else 0,
            content_type=file.content_type,
        )
    except:
        raise
    finally:
        file.data.close()

def remove_object(object_name):
    """Удаление объекта из MinIO"""
    try:
        return minio_client.remove_object(config.MINIO_BUCKET, object_name)
    except S3Error as e:
        print(f"Error while removing file: {e}")
        raise e

def remove_objects(objects):
    """Удаление нескольких объектов из MinIO"""
    try:
        return minio_client.remove_objects(config.MINIO_BUCKET, objects)
    except S3Error as e:
        print(f"Error while removing file: {e}")
        raise e

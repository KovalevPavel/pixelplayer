import logging
import mimetypes
from abc import ABC
from typing import Union

from minio import S3Error
from fastapi import UploadFile, HTTPException
import zipfile
import tarfile
import gzip

from . import MinFile
from .base_min_obj import CHUNK_SIZE
from .stream_wrapper import StreamWrapper
from ...data.file.file_dto import FileCreateDto
from .operations import put_object, remove_object
from ...data.file import file_dto, file_repository


class ArchiveHandler(ABC):
    """
    Абстрактный класс хэндлера
    """
    @classmethod
    def extract_and_upload(cls, upload_file: UploadFile, current_user, result_list: list, custom_dir: Union[str, None] = None):
        """
        Извлечение файлов из архива и последующая загрузка

        Parameters
        ----------
        upload_file : UploadFile
            загружаемый арихв
        current_user
            текущий пользователь
        result_list : list
            список, куда будут записаны метаданные извлеченных и загруженных файлов
        custom_dir : Union[str, None]
            дополнительная директория. Указывается в том случае, если архив загружается не в корень директории пользователя в MinIO
        """
        pass

class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """
    def extract_and_upload(self, upload_file: UploadFile, current_user, result_list: list, custom_dir: Union[str, None] = None):
        with zipfile.ZipFile(upload_file.file) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                with archive.open(member) as f:
                    save_file_stream_to_minio_and_db(f, member.filename, current_user, result_list, custom_dir)

class TarArchiveHandler(ArchiveHandler):
    """
    Хэндлер для tar архивов
    """
    def __init__(self, mode="r:*"):
        self.mode = mode

    def extract_and_upload(self, upload_file: UploadFile, current_user, result_list: list, custom_dir: Union[str, None] = None):
        with tarfile.open(fileobj=upload_file.file, mode=self.mode) as archive:
            for member in archive.getmembers():
                if member.isdir():
                    continue
                f = archive.extractfile(member)
                if f:
                    save_file_stream_to_minio_and_db(f, member.name, current_user, result_list, custom_dir)


class GzArchiveHandler(ArchiveHandler):
    """
    Хэндлер для gz архивов
    """
    def extract_and_upload(self, upload_file: UploadFile, current_user, result_list: list, custom_dir: Union[str, None] = None):
        original_name = upload_file.filename[:-3]  # убираем .gz
        with gzip.open(upload_file.file, 'rb') as gz_file:
            save_file_stream_to_minio_and_db(gz_file, original_name, current_user, result_list, custom_dir)

def _guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def save_file_stream_to_minio_and_db(stream, original_name: str, current_user, result_list: list, custom_dir: Union[str, None] = None):
    """
    Загрузка конкретного файла в MinIO и сохранение метаданных в PostgreSQL

    Parameters
    ----------
    stream
        поток файла
    original_name : str
        имя файла. Представляет собой строку вида <path>/<relative>/<to>/<archive>/<root>/filename.ext
    current_user
        текущий пользователь
    result_list : list
        список, куда будут записаны метаданные извлеченных и загруженных файлов
    custom_dir : Union[str, None]
        дополнительная директория. Указывается в том случае, если архив загружается не в корень директории пользователя в MinIO
    """
    sanitized_dir = custom_dir.strip("/") if custom_dir else None
    minio_object_name = f"{current_user.username}/{original_name}"
    mime_type = _guess_mime_type(original_name)

    # Вычисляем длину (если знаем), иначе MinIO будет читать поток до конца
    content_bytes = stream.read()
    length = len(content_bytes)

    def file_generator():
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    wrapped_stresam = StreamWrapper(file_generator())

    try:
        put_object(MinFile(file_name=minio_object_name, stream_wrapper=wrapped_stresam, content_type=mime_type))

    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {err.code}: {err.message}")

    file_meta = FileCreateDto(
        original_name=f"{sanitized_dir}/{original_name}",
        minio_object_name=minio_object_name,
        size_bytes=length,  # если можно, можно вычислить длину заранее и прокинуть сюда
        mime_type=mime_type
    )

    try:
        db_file = file_repository.create_file(file=file_meta, owner_id=current_user.id)
    except Exception as err:
        # Если ошибка при сохранении в БД — можно удалить файл из MinIO, чтобы не было мусора
        try:
            remove_object(object_name=minio_object_name)
        except S3Error as s3err:
            logging.error(f"Ошибка удаления файла: {s3err.code}: {s3err.message}")

        raise HTTPException(status_code=500, detail=f"Ошибка сохранения метаданных файла: {str(err)}")

    result_list.append(file_dto.FileDto.model_validate(db_file))

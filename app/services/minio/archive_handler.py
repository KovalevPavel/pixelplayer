import gzip
import logging
import mimetypes
import os.path
import tarfile
import uuid
from abc import ABC
from io import BytesIO
from typing import Union

import zipfile
from fastapi import HTTPException, UploadFile
from minio import S3Error

from app.services.minio.encoding import safe_name

from ...data.file import file_dto, file_repository
from ...data.file.file_dto import FileCreateDto
from .base_min_obj import MinFile
from .operations import put_object, remove_object


class ArchiveHandler(ABC):
    """
    Абстрактный класс хэндлера
    """

    @classmethod
    def extract_and_upload(
        cls,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Union[str, None] = None,
    ):
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
            дополнительная директория.
            Указывается в том случае, если архив загружается не в корень директории пользователя в MinIO
        """
        pass


class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Union[str, None] = None,
    ):
        with zipfile.ZipFile(upload_file.file) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                with archive.open(member) as f:
                    save_file_stream_to_minio_and_db(f, safe_name(member), current_user, result_list, custom_dir)


class TarArchiveHandler(ArchiveHandler):
    """
    Хэндлер для tar архивов
    """

    def __init__(self, mode="r:*"):
        self.mode = mode

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Union[str, None] = None,
    ):
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

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Union[str, None] = None,
    ):
        original_name = upload_file.filename[:-3]  # убираем .gz
        with gzip.open(upload_file.file, "rb") as gz_file:
            save_file_stream_to_minio_and_db(gz_file, original_name, current_user, result_list, custom_dir)


def _guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def save_file_stream_to_minio_and_db(
    stream,
    original_name: str,
    current_user,
    result_list: list,
    custom_dir: Union[str, None] = None,
):
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
        дополнительная директория.
        Указывается в том случае, если архив загружается не в корень директории пользователя в MinIO
    """

    # убирам лишнее, если есть
    sanitized_dir = custom_dir.strip("/") if custom_dir else None

    # cтроим путь до файла относительно кастомной директории (если есть)
    final_original_name = f"{sanitized_dir}/{original_name}" if sanitized_dir else original_name

    file_id = str(uuid.uuid4())

    # приведенное имя в структуре minio
    minio_object_name = __get_filename(raw_name=final_original_name, file_id=file_id)
    minio_object_name = f"{current_user.id}/{minio_object_name}"

    mime_type = _guess_mime_type(original_name)

    # Вычисляем длину (если знаем), иначе MinIO будет читать поток до конца
    content_bytes = stream.read()
    length = len(content_bytes)

    try:
        put_object(
            MinFile(
                file_name=minio_object_name,
                data=BytesIO(content_bytes),
                content_type=mime_type,
                length=length,
            )
        )

    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {err.code}: {err.message}")

    file_meta = FileCreateDto(
        id=file_id,
        original_name=final_original_name,
        minio_object_name=minio_object_name,
        size_bytes=length,  # если можно, можно вычислить длину заранее и прокинуть сюда
        mime_type=mime_type,
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


def __get_filename(raw_name: str, file_id: str) -> str:
    minio_filename_data = os.path.basename(raw_name).split(".")
    count = len(minio_filename_data)

    if count == 1:
        ext = None
    else:
        ext = minio_filename_data[-1]

    return f"{file_id}.{ext}" if ext else f"{file_id}"

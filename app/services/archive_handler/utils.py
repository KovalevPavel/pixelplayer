import logging
import mimetypes
import os.path
import re
import uuid
from io import BytesIO
from os import path
from typing import Union

from fastapi import HTTPException
from minio import S3Error

from ...data.file import file_dto, file_repository
from ...data.file.file_dto import FileCreateDto
from ..meta_parser.factory import get_parser
from ..minio.base_min_obj import MinFile
from ..minio.operations import put_object, remove_object


def get_track_number(raw: Union[str, None]) -> int:
    if not raw:
        return -1

    segments = re.findall(r"\d+", raw)

    return int(segments[0]) if len(segments) > 0 else -1


def get_track_title_from_path(raw: str) -> str:
    return path.basename(path.normpath(raw))


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

    parser = get_parser(content_bytes)

    if parser is None:
        # Не получилось распарсить, значит вероятно не аудиофайл. Выходим
        return

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

    meta_from_file = parser.get_metadata()
    title = meta_from_file.track_title

    file_meta = FileCreateDto(
        id=file_id,
        original_name=final_original_name,
        minio_object_name=minio_object_name,
        size_bytes=length,  # если можно, можно вычислить длину заранее и прокинуть сюда
        mime_type=mime_type,
        track_title=title if title else get_track_title_from_path(final_original_name),
        track_number=get_track_number(meta_from_file.track_number),
        album=meta_from_file.album,
        artist=meta_from_file.artist,
        genre=meta_from_file.genre,
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

    result = parser.extract_cover()
    logging.warning(f"cover: {result}")

    result_list.append(file_dto.FileDto.model_validate(db_file))


def _guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def __get_filename(raw_name: str, file_id: str) -> str:
    minio_filename_data = os.path.basename(raw_name).split(".")
    count = len(minio_filename_data)

    if count == 1:
        ext = None
    else:
        ext = minio_filename_data[-1]

    return f"{file_id}.{ext}" if ext else f"{file_id}"

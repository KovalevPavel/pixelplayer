import mimetypes
from abc import ABC

from minio import S3Error
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import zipfile
import tarfile
import gzip

from . import MinFile
from .base_min_obj import MinDirectory, CHUNK_SIZE
from .stream_wrapper import StreamWrapper
from ... import crud
from ...db import schemas
from .operations import put_object, remove_object

class ArchiveHandler(ABC):
    @classmethod
    def extract_and_upload(cls, upload_file: UploadFile, current_user, db: Session, result_list: list):
        pass

class ZipArchiveHandler(ArchiveHandler):
    def extract_and_upload(self, upload_file: UploadFile, current_user, db: Session, result_list: list):
        with zipfile.ZipFile(upload_file.file) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    _save_dir_to_minio(member.filename, current_user)
                    continue
                with archive.open(member) as f:
                    _save_file_stream_to_minio_and_db(f, member.filename, current_user, db, result_list)

class TarArchiveHandler(ArchiveHandler):
    def __init__(self, mode="r:*"):
        self.mode = mode

    def extract_and_upload(self, upload_file: UploadFile, current_user, db: Session, result_list: list):
        with tarfile.open(fileobj=upload_file.file, mode=self.mode) as archive:
            for member in archive.getmembers():
                if member.isdir():
                    _save_dir_to_minio(member.name, current_user)
                    continue
                f = archive.extractfile(member)
                if f:
                    _save_file_stream_to_minio_and_db(f, member.name, current_user, db, result_list)


class GzArchiveHandler(ArchiveHandler):
    def extract_and_upload(self, upload_file: UploadFile, current_user, db: Session, result_list: list):
        original_name = upload_file.filename[:-3]  # убираем .gz
        with gzip.open(upload_file.file, 'rb') as gz_file:
            _save_file_stream_to_minio_and_db(gz_file, original_name, current_user, db, result_list)

def _guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def _save_dir_to_minio(dir_name: str, current_user):
    object_name = f"{current_user.username}/{dir_name.rstrip('/')}/"
    put_object(MinDirectory(dir_name=object_name))
    return object_name

def _save_file_stream_to_minio_and_db(stream, original_name: str, current_user, db: Session, result_list: list):
    object_name = f"{current_user.username}/{original_name}"
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
        put_object(MinFile(file_name=object_name, stream_wrapper=wrapped_stresam, content_type=mime_type))

    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {err.code}: {err.message}")

    file_meta = schemas.FileCreate(
        original_name=original_name,
        minio_object_name=object_name,
        size_bytes=length,  # если можно, можно вычислить длину заранее и прокинуть сюда
        mime_type=mime_type
    )

    try:
        db_file = crud.create_file(db, file=file_meta, owner_id=current_user.id)
    except Exception as err:
        # Если ошибка при сохранении в БД — можно удалить файл из MinIO, чтобы не было мусора
        try:
            remove_object(object_name=object_name)
        except S3Error:
            pass  # логирование сюда
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения метаданных файла: {str(err)}")

    result_list.append(db_file)

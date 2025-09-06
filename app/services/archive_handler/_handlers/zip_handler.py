import uuid
from typing import Optional

import zipfile
from fastapi import UploadFile

from app.db._entities import FileDbDto
from app.services.archive_handler.archive_handler import ArchiveHandler
from app.services.archive_handler.utils import save_file_stream_to_minio_and_db
from app.services.minio.minio_file import MinioFile
from app.services.minio.repository import put_object

from ...meta_parser.factory import get_parser
from .._encoding import safe_name


class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """

    def __init__(self):
        self.zip_file = None

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Optional[str] = None,
    ):
        with zipfile.ZipFile(upload_file.file, "r") as archive:
            self.zip_file = archive
            for member in archive.infolist():
                if member.is_dir():
                    continue
                with archive.open(member) as f:
                    save_file_stream_to_minio_and_db(f, safe_name(member), current_user, result_list, custom_dir)


def process_directory(self, path: str, parent_cover_url: Optional[str] = None):
    """
    Parameters
    ----
    path
        путь внутри архива относительно корня
    parent_cover_url
        ссылка на обложку, унаследованную от родительской директории
    """
    cover_url = self.__find_and_save_cover(path) or parent_cover_url


def __find_and_save_cover(self, path: str) -> Optional[str]:
    """
    Если в папке есть cover.jpg -> сохраняем его в MinIO и возвращаем ссылку
    """
    cover_name = f"{path}/cover.jpg"
    if cover_name in self.zip_file.namelist():
        content: bytes = self.zip_file.read(cover_name)
        # сохраняем файл в MinIO
        object_name = f"covers/{uuid.uuid4()}.jpg"
        obj = MinioFile(
            object_name=f"covers/{uuid.uuid4()}.jpg",
            data=content,
            content_type="image/jpg",
        )
        put_object(obj)
        return object_name
    return None


def __save_audio_file(self, file_name: str, cover_url: Optional[str]):
    content: bytes = self.zip_file.read(file_name)

    parser = get_parser(content)
    if not parser:
        return

    metadata = parser.get_metadata()

    FileDbDto(
        original_name=cover_url,
    )

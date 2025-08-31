from typing import Optional

import zipfile
from fastapi import UploadFile

from app.services.archive_handler.archive_handler import ArchiveHandler
from app.services.archive_handler.utils import save_file_stream_to_minio_and_db

from ..encoding import safe_name


class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Optional[str] = None,
    ):
        with zipfile.ZipFile(upload_file.file) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                with archive.open(member) as f:
                    save_file_stream_to_minio_and_db(f, safe_name(member), current_user, result_list, custom_dir)

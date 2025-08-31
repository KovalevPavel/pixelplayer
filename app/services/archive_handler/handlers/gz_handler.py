import gzip
from typing import Optional

from fastapi import UploadFile

from app.services.archive_handler.archive_handler import ArchiveHandler
from app.services.archive_handler.utils import save_file_stream_to_minio_and_db


class GzArchiveHandler(ArchiveHandler):
    """
    Хэндлер для gz архивов
    """

    def extract_and_upload(
        self,
        upload_file: UploadFile,
        current_user,
        result_list: list,
        custom_dir: Optional[str] = None,
    ):
        original_name = upload_file.filename[:-3]  # убираем .gz
        with gzip.open(upload_file.file, "rb") as gz_file:
            save_file_stream_to_minio_and_db(gz_file, original_name, current_user, result_list, custom_dir)

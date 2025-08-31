import tarfile
from typing import Optional

from fastapi import UploadFile

from app.services.archive_handler.archive_handler import ArchiveHandler
from app.services.archive_handler.utils import save_file_stream_to_minio_and_db


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
        custom_dir: Optional[str] = None,
    ):
        with tarfile.open(fileobj=upload_file.file, mode=self.mode) as archive:
            for member in archive.getmembers():
                if member.isdir():
                    continue
                f = archive.extractfile(member)
                if f:
                    save_file_stream_to_minio_and_db(f, member.name, current_user, result_list, custom_dir)

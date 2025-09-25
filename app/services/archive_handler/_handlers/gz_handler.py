from typing import Optional

from fastapi import UploadFile

from app.services.archive_handler.archive_handler import ArchiveHandler


class GzArchiveHandler(ArchiveHandler):
    """
    Хэндлер для gz архивов
    """

    def extract(self, upload_file: UploadFile, current_user, on_exctract, custom_dir: Optional[str] = None):
        pass

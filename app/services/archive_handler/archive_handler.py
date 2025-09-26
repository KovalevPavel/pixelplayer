from abc import ABC, abstractmethod
from typing import Optional

from app.services.archive_handler.models import ExtractedData

class ArchiveHandler(ABC):
    """
    Абстрактный класс хэндлера
    """

    @abstractmethod
    def extract(
        self,
        zip_path,
        tmp_dir,
        current_user,
        custom_dir: Optional[str] = None,
    ) -> ExtractedData:
        """
        Извлечение файлов из архива

        Parameters
        ----------
        upload_file : UploadFile
            загружаемый арихв
        current_user
            текущий пользователь
        custom_dir : Union[str, None]
            дополнительная директория.
            Указывается в том случае, если архив загружается не в корень директории пользователя в MinIO
        """
        pass

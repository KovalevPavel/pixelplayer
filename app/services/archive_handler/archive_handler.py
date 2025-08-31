from abc import ABC, abstractmethod
from typing import Union

from fastapi import UploadFile


class ArchiveHandler(ABC):
    """
    Абстрактный класс хэндлера
    """

    @abstractmethod
    def extract_and_upload(
        self,
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

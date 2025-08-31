import gzip
import tarfile
from abc import ABC
from typing import Union

import zipfile
from fastapi import UploadFile

from .encoding import safe_name
from .utils import save_file_stream_to_minio_and_db


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

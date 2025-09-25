import logging
import uuid
import zipfile
from typing import List
from typing import Optional

from fastapi import UploadFile

from app.services.archive_handler.archive_handler import ArchiveHandler
from ..models import AudioFileArchivedFile, CoverArchivedFile, ExtractedData
from ...meta_parser.factory import get_parser
from ...meta_parser.metadata import CoverMetaData


class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """

    def __init__(self):
        self.__zip_file = None
        self.__audiofiles: List[AudioFileArchivedFile] = list()
        self.__covers: List[CoverArchivedFile] = list()
        self.__current_user: Optional[str] = None

    def extract(
            self,
            upload_file: UploadFile,
            current_user,
            custom_dir: Optional[str] = None,
    ):
        self.__audiofiles = list()
        self.__covers = list()
        self.__current_user = current_user
        with zipfile.ZipFile(upload_file.file, "r") as archive:
            self.__zip_file = archive
            self.__process_directory("", None)

            self.__current_user = None

            return ExtractedData(
                tracks=self.__audiofiles,
                covers=self.__covers,
            )

    def __process_directory(self, path: str, parent_cover: Optional[CoverArchivedFile] = None):
        """
        Parameters
        ----
        path
            путь внутри архива относительно корня
        parent_cover
            ссылка на обложку, унаследованную от родительской директории
        """
        current_cover = self.__find_and_save_cover(path) or parent_cover

        subdirs = self.__list_subdirs(path)
        files = self.__list_files(path)
        
        # Обрабатываем все аудиофайлы в папке
        for file in files:
            # logging.warning(f"handling file: {file}")
            content = self.__zip_file.read(file)
            handler = get_parser(content_bytes=content)
            if not handler:
                logging.warning(f"not found handler for file: {file}")
                continue

            track_id = str(uuid.uuid4())

            result = AudioFileArchivedFile(
                track_id=track_id,
                original_name=path,
                track_bytes=content,
                cover_id=current_cover.id if current_cover else None,
                metadata=handler.get_metadata(),
            )

            self.__audiofiles.append(result)

        # Рекурсивно идём в поддиректории
        for subdir in subdirs:
            self.__process_directory(subdir, current_cover)

    def __find_and_save_cover(self, path: str) -> Optional[CoverArchivedFile]:
        """
        Если в папке есть cover.jpg -> сохраняем его и возвращаем ссылку
        """
        p = path.lstrip("/")
        cover_name = f"{p}/cover.jpg"
        if cover_name in self.__zip_file.namelist():
            content: bytes = self.__zip_file.read(cover_name)
            cover_id = str(uuid.uuid4())

            # путь до обложки в MinIO
            object_name = f"{self.__current_user}/covers/{cover_id}.jpg"

            obj = CoverArchivedFile(
                cover_id=cover_id,
                original_name=object_name,
                cover_bytes=content,
                metadata=CoverMetaData(
                    mime="image/jpg",
                    width=None,
                    heigth=None,
                    bytes=content,
                    format="jpg"
                )
            )

            self.__covers.append(obj)
            return obj
        return None

    def __list_files(self, path: str) -> list[str]:
        """Вернет список файлов (без директорий) внутри указанного path."""
        p = path.lstrip("/")
        return [
            name for name in self.__zip_file.namelist()
            if name.startswith(p)
               and "/" not in name[len(p) + 1:]
               and not name.endswith("/")
        ]


    def __list_subdirs(self, path: str) -> list[str]:
        """Вернет список поддиректорий внутри указанного path."""
        subdirs = set()
        for name in self.__zip_file.namelist():
            if name.startswith(path) and name != path:
                parts = name[len(path):].strip("/").split("/", 1)
                if len(parts) > 1:
                    subdirs.add(f"{path}/{parts[0]}")
        return list(subdirs)

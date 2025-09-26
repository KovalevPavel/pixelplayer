import logging
import mimetypes
import os
from pathlib import Path
import uuid
import zipfile
from typing import List
from typing import Optional


from app.services.archive_handler.archive_handler import ArchiveHandler
from ..models import AudioFileArchivedFile, CoverArchivedFile, ExtractedData
from ...meta_parser.factory import get_parser
from ...meta_parser.metadata import CoverMetaData


class ZipArchiveHandler(ArchiveHandler):
    """
    Хэндлер для zip архивов
    """

    def __init__(self):
        self.__audiofiles: List[AudioFileArchivedFile] = list()
        self.__covers: List[CoverArchivedFile] = list()
        self.__current_user: Optional[str] = None

    def extract(
            self,
            zip_path,
            tmp_dir,
            current_user,
            custom_dir: Optional[str] = None,
    ):
        self.__audiofiles = list()
        self.__covers = list()
        self.__current_user = current_user

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(tmp_dir)
            self.__process_directory(tmp_dir, None)

            # self.__current_user = None

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
            filepath = f"{path}/{file}"
            handler = get_parser(file=filepath)
            if not handler:
                logging.warning(f"Could not find handler for file: {file}")
                continue

            track_id = str(uuid.uuid4())

            result = AudioFileArchivedFile(
                track_id=track_id,
                original_name=filepath,
                cover_id=current_cover.id if current_cover else None,
                metadata=handler.get_metadata(name=filepath),
            )

            self.__audiofiles.append(result)

        # Рекурсивно идём в поддиректории
        for subdir in subdirs:
            self.__process_directory(subdir, current_cover)

    def __find_and_save_cover(self, path: str) -> Optional[CoverArchivedFile]:
        """
        Если в папке есть cover.jpg -> сохраняем его и возвращаем ссылку
        """
        cover_name = f"{path}/cover.jpg"
        if os.path.exists(cover_name):
            content: bytes = Path(cover_name).read_bytes()
            cover_id = str(uuid.uuid4())

            # путь до обложки в MinIO
            object_name = f"{self.__current_user}/covers/{cover_id}.jpg"

            mimetype, _ = mimetypes.guess_type(cover_name)

            obj = CoverArchivedFile(
                cover_id=cover_id,
                original_name=object_name,
                cover_bytes=content,
                metadata=CoverMetaData(
                    mime=mimetype,
                    width=None,
                    heigth=None,
                    bytes=content,
                    format="jpg",
                ),
            )

            self.__covers.append(obj)
            return obj
        return None

    def __list_files(self, path: str) -> list[str]:
        """Вернет список файлов (без директорий) внутри указанного path."""
        return [name for name in os.listdir(path) if name.endswith(".mp3")]

    def __list_subdirs(self, path: str) -> list[str]:
        """Вернет список поддиректорий внутри указанного path."""
        subdirs = set()
        for name in os.listdir(path):
            raw_path = f"{path}/{name}"
            if os.path.isdir(raw_path):
                subdirs.add(raw_path)
        return list(subdirs)

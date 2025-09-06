from typing import Optional

from ._handlers.gz_handler import GzArchiveHandler
from ._handlers.tar_handler import TarArchiveHandler
from ._handlers.zip_handler import ZipArchiveHandler
from .archive_handler import ArchiveHandler

__handlers_map = {
    ".zip": ZipArchiveHandler(),
    ".tar": TarArchiveHandler("r:"),
    ".tar.gz": TarArchiveHandler("r:gz"),
    ".tgz": TarArchiveHandler("r:gz"),
    ".gz": GzArchiveHandler(),
}


def get_archive_handler(filename: str) -> Optional[ArchiveHandler]:
    for ext, handler in __handlers_map.items():
        if filename.endswith(ext):
            return __handlers_map[ext]
    return None

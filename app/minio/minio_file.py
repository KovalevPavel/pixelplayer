from abc import ABC
from dataclasses import dataclass


class BaseMinObj(ABC):
    """
    Объект, который может быть сохранен в MinIO
    """

@dataclass(frozen=True)
class MinioFile(BaseMinObj):
    """
    Файл, который может быть сохранен в MinIO

    Attributes
    ---
    object_name
        имя (относительно корня бакета), под которым файл будет сохранен
    data
        байты файла
    content_type
        тип контента
    """

    object_name: str
    data: bytes
    content_type: str

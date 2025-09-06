from abc import ABC, abstractmethod
from dataclasses import dataclass


class BaseMinObj(ABC):
    """
    Объект, который может быть сохранен в MinIO
    """

    @property
    @abstractmethod
    def object_name(self) -> str:
        pass

    @property
    @abstractmethod
    def data(self) -> bytes:
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        pass


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

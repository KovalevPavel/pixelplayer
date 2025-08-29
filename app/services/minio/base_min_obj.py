from abc import ABC
from io import BytesIO


class BaseMinObj(ABC):
    """
    Объект, который может быть сохранен в MinIO
    """
    object_name: str
    data: BytesIO
    length: int
    content_type: str
    path: str

class MinFile(BaseMinObj):
    """
    Файл
    """
    def __init__(self, file_name: str, data: BytesIO, content_type: str, length: int):
        self.content_type = content_type
        self.data = BytesIO(data.read())
        self.object_name = file_name
        self.length = length

from abc import ABC
from io import BytesIO

from app.services.minio.stream_wrapper import StreamWrapper

CHUNK_SIZE = 5 * 1024 * 1024

class BaseMinObj(ABC):
    object_name: str
    data: BytesIO
    length: int
    content_type: str

class MinFile(BaseMinObj):
    def __init__(self, file_name: str, stream_wrapper: StreamWrapper, content_type: str):
        self.content_type = content_type
        self.data = stream_wrapper
        self.object_name = file_name

    data: StreamWrapper
    length = -1

class MinDirectory(BaseMinObj):
    def __init__(self, dir_name: str):
        self.object_name = dir_name

    data = BytesIO(b"")
    length = 0
    content_type = "application/x-directory"
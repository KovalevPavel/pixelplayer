class BaseFileParams:
    """
    Параметры сохранения объекта в MinIO
    """
    pass

class Chunk(BaseFileParams):
    """
    Параметры сохранения "по кускам"
    """
    def __init__(self, first_byte: int, length: int):
        self.first_byte = first_byte
        self.length = length

    first_byte: int
    length: int

class Full(BaseFileParams):
    """
    Сохранение объекта целиком
    """
    def __init__(self, file_length):
        self.file_length = file_length

    file_length: int

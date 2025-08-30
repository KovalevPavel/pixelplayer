import io


class StreamWrapper(io.RawIOBase):
    """
    Обертка для stream'а
    """

    def __init__(self, generator):
        super().__init__()
        self.generator = generator
        self.buffer = b""

    def readable(self):
        return True

    def readinto(self, b):
        try:
            while len(self.buffer) < len(b):
                self.buffer += next(self.generator)
        except StopIteration:
            pass  # Генератор исчерпан

        n = min(len(b), len(self.buffer))
        b[:n] = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return n

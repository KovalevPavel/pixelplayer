from io import BytesIO
from typing import Optional

from PIL import Image, UnidentifiedImageError

from .metadata import CoverMetaData


def detect_mime_from_bytes(data: bytes) -> str:
    """
    Определяем MIME-тип картинки из raw-байт.
    """
    try:
        with Image.open(BytesIO(data)) as img:
            fmt = img.format  # "JPEG", "PNG", "WEBP", ...
            if fmt:
                return Image.MIME.get(fmt, "application/octet-stream")
    except UnidentifiedImageError:
        return "application/octet-stream"

    return "application/octet-stream"


def cover_info(cover_bytes: bytes, mime: Optional[str] = None) -> Optional[CoverMetaData]:
    """
    Достаём инфу об обложке: mime, размеры, формат, raw-байты.
    """
    if not cover_bytes:
        return None

    if mime is None:
        mime = detect_mime_from_bytes(cover_bytes)

    try:
        with Image.open(BytesIO(cover_bytes)) as img:
            return CoverMetaData(
                mime=mime,
                width=img.width,
                heigth=img.height,
                format=img.format,
                bytes=cover_bytes,
            )
    except UnidentifiedImageError:
        return None

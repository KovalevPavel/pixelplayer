import logging
import unicodedata

logger = logging.getLogger(__name__)


def normalize_filename(raw_filename: str) -> str:
    """
    Нормализует имя файла в UTF-8 NFC.
    Если имя пришло уже валидное, вернёт его без ошибок.
    Если имя было с нечитаемыми символами (latin-1 в utf-8), попробует восстановить.
    """

    result = raw_filename

    for encoding in ("latin-1", "cp1251"):
        try:
            fixed = raw_filename.encode(encoding).decode("utf-8")
            result = fixed
            break
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    if result != raw_filename:
        logger.info(f"Filename recovered from {raw_filename!r} → {result!r}")
    else:
        logger.warning(f"Filename left unchanged (could not decode): {raw_filename!r}")

    # Финальная нормализация в NFC (рекомендуемый формат для хранения в БД)
    return unicodedata.normalize("NFC", result)

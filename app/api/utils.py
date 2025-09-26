import logging
import unicodedata

from fastapi import HTTPException, Request
from jose import JWTError, jwt

from ..core.config import ALGORITHM, SECRET_KEY

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

def __get_token(request: Request) -> str:
    try:
        auth_header = request.headers["Authorization"]
    except KeyError:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not auth_header or not auth_header.startswith("Bearer"):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    user_token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(user_token, SECRET_KEY, algorithms=ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    return payload


def get_user_id(request: Request) -> str:
    user_token = __get_token(request)
    return user_token["user_id"]
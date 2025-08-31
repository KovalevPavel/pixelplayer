import logging
import unicodedata

import zipfile

logger = logging.getLogger(__name__)


def safe_name(info: zipfile.ZipInfo) -> str:
    raw_bytes = info.filename.encode("cp437")
    try:
        name = raw_bytes.decode("cp866")
        # проверяем, есть ли кириллица
        if any("А" <= c <= "я" for c in name):
            return unicodedata.normalize("NFC", name)
        else:
            logger.warning("Unable to find cyryllic symbols")
            return info.filename
    except UnicodeDecodeError:
        logger.error(f"Exception while decoding {info.filename}")
        return info.filename

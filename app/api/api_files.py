import logging
from typing import List, Optional, Union

from fastapi import APIRouter, Depends
from fastapi import File as FastAPIFile
from fastapi import Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.services.archive_handler.archive_handler import (
    GzArchiveHandler,
    TarArchiveHandler,
    ZipArchiveHandler,
    save_file_stream_to_minio_and_db,
)

from ..data.auth import auth_repository
from ..data.file import file_dto, file_repository
from ..db.db_dto import UserDbDto
from ..services.minio.operations import get_object, remove_object

fileRouter = APIRouter(prefix="/files")


@fileRouter.post("/upload", response_model=List[file_dto.FileDto])
async def upload_files(
    files_list: List[UploadFile] = FastAPIFile(...),
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
    custom_dir: Union[str, None] = None,
):
    """
    Загружает файлы и архивы (zip, tar, tar.gz, tgz, gz) в MinIO
    """
    uploaded_files_metadata = []

    handlers_map = {
        ".zip": ZipArchiveHandler(),
        ".tar": TarArchiveHandler("r:"),
        ".tar.gz": TarArchiveHandler("r:gz"),
        ".tgz": TarArchiveHandler("r:gz"),
        ".gz": GzArchiveHandler(),
    }

    for file in files_list:
        filename = file.filename.lower()
        matched_handler = None
        for ext, handler in handlers_map.items():
            if filename.endswith(ext):
                matched_handler = handler
                break

        if matched_handler:
            matched_handler.extract_and_upload(file, current_user, uploaded_files_metadata, custom_dir)
        else:
            save_file_stream_to_minio_and_db(file.file, file.filename, current_user, uploaded_files_metadata)

    return uploaded_files_metadata


@fileRouter.get("/all", response_model=List[file_dto.FileDto])
def get_all_files(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
):
    """Получает список файлов пользователя с возможностью поиска."""
    return file_repository.get_files_by_owner(owner_id=current_user.id, skip=skip, limit=limit, search=search)


@fileRouter.get("/get", response_model=file_dto.FileDto)
async def get_file(
    file_id: str,
    range_header: Optional[str] = Header(None, alias="Range"),
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
):
    """Скачивает файл, поддерживая частичную загрузку (byte range)."""

    from ..services.minio.offset_handler import Chunk, Full

    db_file = file_repository.get_file(file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    try:
        if range_header:
            # Частичная загрузка
            import re

            byte1, byte2 = 0, db_file.size_bytes - 1
            match = re.search(r"(\d+)-(\d*)", range_header)
            if match:
                g1, g2 = match.groups()
                if g1:
                    byte1 = int(g1)
                if g2:
                    byte2 = int(g2)

            length = byte2 - byte1 + 1
            stream = get_object(
                object_name=db_file.minio_object_name,
                params=Chunk(first_byte=byte1, length=length),
            )

            headers = {
                "Content-Range": f"bytes {byte1}-{byte2}/{db_file.size_bytes}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": db_file.mime_type,
            }
            return StreamingResponse(stream, status_code=206, headers=headers, media_type=db_file.mime_type)
        else:
            # Полная загрузка
            stream = get_object(
                object_name=db_file.minio_object_name,
                params=Full(file_length=db_file.size_bytes),
            )
            return StreamingResponse(stream, media_type=db_file.mime_type)

    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@fileRouter.delete("/remove", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
):
    """Удаляет файл из MinIO и его метаданные из PostgreSQL."""
    db_file = file_repository.get_file(file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    # Удаление из MinIO
    remove_object(object_name=db_file.minio_object_name)

    # Удаление из БД
    file_repository.delete_file(file_id=file_id)

    return


@fileRouter.get("/all_files", response_model=List[file_dto.FileDto])
async def files():
    return file_repository.get_all_files()

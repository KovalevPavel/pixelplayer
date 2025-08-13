import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.minio.archive_handler import ZipArchiveHandler, TarArchiveHandler, GzArchiveHandler, _save_file_stream_to_minio_and_db
from .. import crud
from ..db import  schemas
from ..core.security import get_current_active_user
from ..db.database import get_db
# from app.services.minio_client import minio_client, config
from ..services.minio.operations import get_object, remove_object

fileRouter = APIRouter(prefix="/files")

@fileRouter.post("/upload", response_model=List[schemas.File])
async def upload_files(
    files: List[UploadFile] = FastAPIFile(...),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Загружает файлы и архивы (zip, tar, tar.gz, tgz, gz) в MinIO.
    Директории в архивах тоже создаются в MinIO.
    """
    uploaded_files_metadata = []

    handlers_map = {
        ".zip": ZipArchiveHandler(),
        ".tar": TarArchiveHandler("r:"),
        ".tar.gz": TarArchiveHandler("r:gz"),
        ".tgz": TarArchiveHandler("r:gz"),
        ".gz": GzArchiveHandler(),
    }

    for file in files:
        filename = file.filename.lower()
        matched_handler = None
        for ext, handler in handlers_map.items():
            if filename.endswith(ext):
                matched_handler = handler
                break

        if matched_handler:
            matched_handler.extract_and_upload(file, current_user, db, uploaded_files_metadata)
        else:
            _save_file_stream_to_minio_and_db(file.file, file.filename, current_user, db, uploaded_files_metadata)

    return uploaded_files_metadata

@fileRouter.get("/all", response_model=List[schemas.File])
def get_all_files(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получает список файлов пользователя с возможностью поиска."""
    files = crud.get_files_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit, search=search)
    return files

@fileRouter.get("/get", response_model=schemas.File)
async def get_file(
    file_id: int,
    request: Request,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Скачивает файл, поддерживая частичную загрузку (byte range)."""

    from ..services.minio import Chunk
    from ..services.minio import Full

    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    range_header = request.headers.get("Range")

    try:
        if range_header:
            # Частичная загрузка
            byte1, byte2 = 0, db_file.size_bytes - 1
            if range_header:
                match = re.search(r"(\d+)-(\d*)", range_header)
                groups = match.groups()
                if groups[0]: byte1 = int(groups[0])
                if groups[1]: byte2 = int(groups[1])

            length = byte2 - byte1 + 1
            stream = get_object(object_name=db_file.minio_object_name, params=Chunk(first_byte=byte1, length=length))

            headers = {
                'Content-Range': f'bytes {byte1}-{byte2}/{db_file.size_bytes}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(length),
                'Content-Type': db_file.mime_type
            }
            return StreamingResponse(stream, status_code=206, headers=headers)
        else:
            # Полная загрузка
            response = get_object(object_name=db_file.minio_object_name, params=Full(db_file.size_bytes))
            stream = response.stream(db_file.size_bytes)
            response.close()
            return StreamingResponse(stream, media_type=db_file.mime_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@fileRouter.delete("/remove", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удаляет файл из MinIO и его метаданные из PostgreSQL."""
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    # Удаление из MinIO
    remove_object(object_name=db_file.minio_object_name)

    # Удаление из БД
    crud.delete_file(db, file_id=file_id)

    return

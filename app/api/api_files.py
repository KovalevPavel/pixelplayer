import logging
import mimetypes
from typing import List, Optional, Union

from fastapi import APIRouter, Depends
from fastapi import File as FastAPIFile
from fastapi import Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.db import audio_repository

from ..authorization import auth_repository
from ..core.models.file_dto import CoverInDto, FileDto, FileCreateDto
from ..core.models.user_dto import UserBaseDto
from ..minio import minio_repository
from ..minio.minio_file import MinioFile
from ..services.archive_handler.factory import get_archive_handler

fileRouter = APIRouter(prefix="/files")


@fileRouter.post("/upload", response_model=List[FileDto])
def upload_files(
        files_list: List[UploadFile] = FastAPIFile(...),
        current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
        custom_dir: Union[str, None] = None,
):
    """
    Загружает файлы и архивы (zip, tar, tar.gz, tgz, gz) в MinIO
    """
    uploaded_files_metadata = []

    for file in files_list:
        filename = file.filename.lower()
        matched_handler = get_archive_handler(filename)

        if matched_handler:
            data = matched_handler.extract(upload_file=file, current_user=current_user.id, custom_dir=custom_dir)

            for cover in data.covers:
                mime_type, _ = mimetypes.guess_type(cover.original_name)

                audio_repository.create_cover_file(
                    file=CoverInDto(
                        id=cover.id,
                        minio_object_name=cover.original_name,
                    ),
                )

                minio_repository.put_object(
                    MinioFile(
                        object_name=cover.original_name,
                        data=cover.bytes,
                        content_type=mime_type,
                    )
                )


            for audio_file in data.tracks:
                minio_object_name = f"{current_user.id}/{audio_file.id}.mp3"
                mime_type, _ = mimetypes.guess_type(minio_object_name)

                audio_repository.create_audio_file(
                    file = FileCreateDto(
                        id=audio_file.id,
                        original_name=audio_file.original_name,
                        size_bytes=len(audio_file.content_bytes),
                        minio_object_name=minio_object_name,
                        track_title=audio_file.metadata.track_title,
                        track_number=audio_file.metadata.track_number,
                        artist=audio_file.metadata.artist,
                        album=audio_file.metadata.album,
                        mime_type=mime_type,
                        genre=audio_file.metadata.genre,
                        cover=audio_file.cover_id,
                    ),
                    owner_id=current_user.id,
                )

                minio_repository.put_object(
                    MinioFile(
                        object_name=minio_object_name,
                        data=audio_file.content_bytes,
                        content_type= mime_type,
                    )
                )
                

            tracks = list(
                map(
                    lambda tr: FileDto(
                        id=tr.id,
                        original_name=tr.original_name,
                        size_bytes=len(tr.content_bytes),
                        minio_object_name=f"{current_user.id}/{tr.id}.mp3",
                        track_title=tr.metadata.track_title,
                        track_number=int(tr.metadata.track_number),
                        album=tr.metadata.album,
                        artist=tr.metadata.artist,
                        genre=None,
                        cover=tr.cover_id,
                        mime_type="music/mp3",
                    ),
                    data.tracks,
                ),
            )

            uploaded_files_metadata=tracks

    return uploaded_files_metadata


@fileRouter.get("/all", response_model=List[FileDto])
def get_all_files(
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
):
    """Получает список файлов пользователя с возможностью поиска."""
    return audio_repository.get_files_by_owner(owner_id=current_user.id, skip=skip, limit=limit, search=search)


@fileRouter.get("/get", response_model=FileDto)
async def get_file(
        file_id: str,
        range_header: Optional[str] = Header(None, alias="Range"),
        current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
):
    """Скачивает файл, поддерживая частичную загрузку (byte range)."""

    from ..minio.minio_file_params import Chunk, Full

    db_file = audio_repository.get_file(file_id=file_id)
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
            stream = minio_repository.get_object(
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
            stream = minio_repository.get_object(
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
        current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
):
    """Удаляет файл из MinIO и его метаданные из PostgreSQL."""
    db_file = audio_repository.get_file(file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this file")

    # Удаление из MinIO
    minio_repository.remove_object(object_name=db_file.minio_object_name)

    # Удаление из БД
    audio_repository.delete_file(file_id=file_id)

    return


@fileRouter.get("/all_files", response_model=List[FileDto])
async def files():
    return audio_repository.get_all_files()

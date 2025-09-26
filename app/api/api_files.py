import logging
import os
from pathlib import Path
import tempfile
import shutil
import time
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Request, Response
from fastapi import File as FastAPIFile
from fastapi import Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from jose import jwt
from jose.exceptions import JWTError

from app.api.utils import get_user_id
from app.db import audio_repository
from app.services.decoding.decoding import convert_audio

from ..authorization import auth_repository
from ..core.models.file_dto import CoverInDto, FileDto, FileCreateDto
from ..core.config import ALGORITHM, FAST_API_DOMAIN, HLS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from ..core.models.user_dto import UserBaseDto
from ..minio import minio_repository
from ..minio.minio_file import MinioFile
from ..services.archive_handler.factory import get_archive_handler

fileRouter = APIRouter(prefix="/files")
internalRouter = APIRouter(prefix="/internal")


@fileRouter.post("/upload", response_model=List[FileDto])
async def upload_files(
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
            with tempfile.TemporaryDirectory() as tmpdir:
                # Сохраняем zip во временный файл
                zip_path = os.path.join(tmpdir, file.filename)
                with open(zip_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)

                data = matched_handler.extract(
                    zip_path=zip_path,
                    tmp_dir=tmpdir,
                    current_user=current_user.id,
                    custom_dir=custom_dir,
                )

                for cover in data.covers:
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
                            content_type=cover.metadata.mime,
                        )
                    )
                
                minio_dir = f"{tmpdir}/minio"


                for audio_file in data.tracks:

                    convert_audio(
                        file_id=audio_file.id,
                        file_path=audio_file.original_name,
                        output_path=minio_dir,
                    )

                    audio_repository.create_audio_file(
                        file = FileCreateDto(
                            id=audio_file.id,
                            original_name=audio_file.original_name,
                            size_bytes=5,
                            minio_object_name=audio_file.id,
                            track_title=audio_file.metadata.track_title,
                            track_number=audio_file.metadata.track_number,
                            artist=audio_file.metadata.artist,
                            album=audio_file.metadata.album,
                            mime_type=audio_file.metadata.mime,
                            genre=audio_file.metadata.genre,
                            cover=audio_file.cover_id,
                        ),
                        owner_id=current_user.id,
                    )

                    for ff in os.listdir(f"{minio_dir}/{audio_file.id}"):
                        minio_repository.put_object(
                            MinioFile(
                                object_name=f"{current_user.id}/{audio_file.id}/{ff}",
                                data=Path(f"{minio_dir}/{audio_file.id}/{ff}").read_bytes(),
                                content_type= audio_file.metadata.mime,
                            )
                        )
                

                tracks = list(
                    map(
                        lambda tr: FileDto(
                            id=tr.id,
                            original_name=tr.original_name,
                            minio_object_name=f"{current_user.id}/{tr.id}.mp3",
                            track_title=tr.metadata.track_title,
                            track_number=int(tr.metadata.track_number),
                            album=tr.metadata.album,
                            artist=tr.metadata.artist,
                            genre=tr.metadata.genre,
                            cover=tr.cover_id,
                            mime_type=tr.metadata.mime,
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

@fileRouter.get("/play/{track_id}")
async def get_playlist_url(track_id: str):
    expire = time.time()*1000 + int(HLS_TOKEN_EXPIRE_MINUTES)*60*1000
    to_encode = {
        "exp": expire,
        "subject": track_id  # В "subject" токена кладем ID трека
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    playlist_url = f"{FAST_API_DOMAIN}/hls/{track_id}/playlist.m3u8?token={encoded_jwt}"
    
    return {"playlist_url": playlist_url}

@internalRouter.get("/verify-hls")
async def verify_hls_token(request: Request, x_original_uri: str | None = Header(None)):
    """
    Внутренний эндпоинт для проверки токена доступа к HLS.
    Вызывается Nginx через auth_request.
    """
    try:
        # user_id = get_user_id(request)
        user_id = "db7267a8-377b-49cb-a92c-29106b0ff882"
    except JWTError:
        raise

    if not x_original_uri:
        raise HTTPException(status_code=400, detail="Missing X-Original-URI header")

    try:
        # Nginx передает нам оригинальный URI, например /hls/track123/playlist.m3u8?token=...
        # 1. Извлекаем токен из query-параметров
        token = None
        if x_original_uri and "token=" in x_original_uri:
            from urllib.parse import parse_qs, urlparse
            query = urlparse(x_original_uri).query
            token = parse_qs(query).get("token", [None])[0]
        if not token:
            raise HTTPException(status_code=401, detail="Token not found")

        # 2. Извлекаем ID трека из пути URI
        # /hls/track123/playlist.m3u8 -> track123
        path_parts = x_original_uri.split("?")[0].split("/")
        # path_parts будет ['','hls','track123', 'playlist.m3u8']
        if len(path_parts) < 3 or path_parts[1] != 'hls':
            raise HTTPException(status_code=400, detail="Invalid URI format")
        track_id_from_url = path_parts[2]

        # 3. Декодируем и валидируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        track_id_from_token: str = payload.get("subject")

        # 4. Главная проверка: ID трека в токене должен совпадать с ID трека в URL
        if track_id_from_token != track_id_from_url:
            raise HTTPException(status_code=403, detail="Token-URL mismatch")

    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    except HTTPException as e:
        # Перехватываем свои же ошибки, чтобы Nginx получил правильный код
        raise e
    except Exception:
        # На случай непредвиденных ошибок парсинга
        raise HTTPException(status_code=400, detail="Bad request")

    # Если все проверки пройдены, возвращаем 200 OK. Nginx получит этот ответ
    # и продолжит выполнение запроса (отдаст файл из MinIO).
    response = Response(status_code=200)
    response.headers["X-User-ID"] = user_id
    return response
    
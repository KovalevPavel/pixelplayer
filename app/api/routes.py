import shutil
import uuid
import zipfile
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Header, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..core.security import get_current_active_user, create_access_token
from ..db.database import get_db
from ..services.minio_client import minio_client, config

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --- Authentication ---
@router.post("/auth", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.OAuth2PasswordRequestForm = Depends()):
    """
    Авторизация пользователя
    """
    # В FastAPI form_data приходит из `application/x-www-form-urlencoded`
    db = next(get_db())
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создает пользователя
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# --- File Operations ---
@router.post("/upload/", response_model=List[schemas.File])
async def upload_files(
    files: List[UploadFile] = FastAPIFile(...),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Загружает один или несколько файлов. Если файл - zip, распаковывает его.
    """
    uploaded_files_metadata = []
    
    for file in files:
        # Если это zip-архив
        if file.content_type == 'application/zip':
            with zipfile.ZipFile(BytesIO(await file.read()), 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    if zip_info.is_dir():
                        continue # Пропускаем директории
                    
                    with zip_ref.open(zip_info) as unzipped_file:
                        file_bytes = unzipped_file.read()
                        file_size = len(file_bytes)
                        object_name = f"user_{current_user.id}/{uuid.uuid4()}_{zip_info.filename}"
                        
                        minio_client.put_object(
                            config.MINIO_BUCKET,
                            object_name,
                            BytesIO(file_bytes),
                            length=file_size,
                            content_type=file.content_type
                        )
                        
                        file_meta = schemas.FileCreate(
                            original_name=zip_info.filename,
                            minio_object_name=object_name,
                            size_bytes=file_size,
                            mime_type=file.content_type
                        )
                        db_file = crud.create_file(db, file=file_meta, owner_id=current_user.id)
                        uploaded_files_metadata.append(db_file)
        else:
            # Обычный файл
            contents = await file.read()
            file_size = len(contents)
            object_name = f"user_{current_user.id}/{uuid.uuid4()}_{file.filename}"
            
            minio_client.put_object(
                config.MINIO_BUCKET,
                object_name,
                BytesIO(contents),
                length=file_size,
                content_type=file.content_type
            )
            
            file_meta = schemas.FileCreate(
                original_name=file.filename,
                minio_object_name=object_name,
                size_bytes=file_size,
                mime_type=file.content_type
            )
            db_file = crud.create_file(db, file=file_meta, owner_id=current_user.id)
            uploaded_files_metadata.append(db_file)

    return uploaded_files_metadata


@router.get("/files/", response_model=List[schemas.File])
def get_user_files(
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получает список файлов пользователя с возможностью поиска."""
    files = crud.get_files_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit, search=search)
    return files


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    request: Request,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Скачивает файл, поддерживая частичную загрузку (byte range)."""
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
            response = minio_client.get_object(config.MINIO_BUCKET, db_file.minio_object_name, offset=byte1, length=length)
            
            headers = {
                'Content-Range': f'bytes {byte1}-{byte2}/{db_file.size_bytes}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(length),
                'Content-Type': db_file.mime_type
            }
            return StreamingResponse(response.stream(length), status_code=206, headers=headers)
        else:
            # Полная загрузка
            response = minio_client.get_object(config.MINIO_BUCKET, db_file.minio_object_name)
            return StreamingResponse(response.stream(db_file.size_bytes), media_type=db_file.mime_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
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
    minio_client.remove_object(config.MINIO_BUCKET, db_file.minio_object_name)
    
    # Удаление из БД
    crud.delete_file(db, file_id=file_id)
    return

# --- Web Interface ---
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Простой HTML интерфейс для демонстрации."""
    return templates.TemplateResponse("index.html", {"request": request})

from typing import Union

from minio import S3Error
from fastapi import HTTPException
from minio.deleteobjects import DeleteObject
from sqlalchemy.orm import Session
from ..db import models, schemas
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..core.security import get_password_hash, verify_password
from ..services.minio import list_objects, remove_objects

def get_user(db: Session, user_id: int):
    smth = select(models.User).where(models.User.id == user_id)
    with(db):
        return db.scalars(smth).first()

def delete_user(db: Session, user_id: int):
    db_user = (
        db.query(models.User)
        .options(selectinload(models.User.files))
        .filter(models.User.id == user_id)
        .first()
    )

    if not db_user:
        return None

    user_prefix = db_user.username

    try:
        # Проверяем, есть ли объекты с таким префиксом
        objects_to_delete = list(list_objects(user_prefix=user_prefix))

        print(f"REMOVED_TO_USER:::{user_prefix}")
        print(f"REMOVED_TO:::{objects_to_delete}")
        if not objects_to_delete:
            return None

        # Формируем генератор для удаления пачкой
        delete_objects = (DeleteObject(obj.object_name) for obj in objects_to_delete)
        for obj in objects_to_delete:
            print(f"DELETE:::{obj.object_name}")
        errors = remove_objects(delete_objects)
        # Логируем ошибки
        for err in errors:
            print(f"Ошибка удаления файла {err.object_name}: {err}")

        # Удаляем пользователя (файлы в БД удалятся каскадно)
        db.delete(db_user)
        db.commit()

        return db_user
    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении из MinIO: {err.message}")

def get_user_by_username(db: Session, username: str) -> Union[models.User, None]:
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_all_users(db: Session):
    smth = select(models.User)
    with db:
        return db.scalars(smth).all()

"""
Репозиторий для получения данных из БД
"""

import logging
from typing import List, Union

from fastapi import HTTPException
from minio import S3Error
from minio.deleteobjects import DeleteObject
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db

from ...db.db_dto import UserDbDto
from ...services.minio.operations import list_objects, remove_objects
from ..utils import get_string_hash
from .user_dto import UserCreateDto


def get_user(user_id: str):
    """
    Получение пользователя из БД
    """
    smth = select(UserDbDto).where(UserDbDto.id == user_id)
    with next(get_db()) as session:
        return session.scalars(smth).first()


def delete_user(user_id: str):
    """
    Удаление пользователя из БД
    """

    smth = select(UserDbDto).options(selectinload(UserDbDto.files)).where(UserDbDto.id == user_id)

    with next(get_db()) as session:
        db_user = session.scalar(smth)

        if not db_user:
            return None

        user_prefix = db_user.id

        try:
            # Проверяем, есть ли объекты с таким префиксом
            objects_to_delete = list(list_objects(user_prefix=user_prefix))

            if not objects_to_delete:
                return None

            # Формируем генератор для удаления пачкой
            delete_objects = (DeleteObject(obj.object_name) for obj in objects_to_delete)
            errors = remove_objects(delete_objects)
            # Логируем ошибки
            for err in errors:
                logging.error(f"Ошибка удаления файла {err.object_name}: {err}")

            # Удаляем пользователя (файлы в БД удалятся каскадно)
            session.delete(db_user)
            session.commit()

            return db_user
        except S3Error as err:
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении из MinIO: {err.message}")


def get_user_by_username(username: str) -> Union[UserDbDto, None]:
    """
    Получение информации о пользователе по его имени
    """
    smth = select(UserDbDto).where(UserDbDto.username == username)
    with next(get_db()) as session:
        return session.scalar(smth)


def create_user(user: UserCreateDto):
    """
    Создание нового пользователя
    """
    hashed_password = get_string_hash(user.password)
    db_user = UserDbDto(username=user.username, hashed_password=hashed_password)
    with next(get_db()) as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user


def get_all_users() -> List[UserDbDto]:
    """
    Получение всех пользователей (использовать только для отладки)
    """
    smth = select(UserDbDto)
    with next(get_db()) as session:
        return session.scalars(smth).all()

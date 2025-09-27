from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from passlib.hash import argon2

from app.core.models.user_dto import UserBaseDto, UserCreateDto
from app.db._database import get_db
from app.db._entities import UserDbEntity

from ._utils import get_string_hash


def verify_password(plain_password, hashed_password):
    """Верификация пароля"""
    return argon2.verify(plain_password, hashed_password)


def get_user(user_id: str) -> UserDbEntity:
    """
    Получение пользователя из БД
    """
    smth = select(UserDbEntity).where(UserDbEntity.id == user_id)
    with next(get_db()) as session:
        return session.scalar(smth)


def delete_user(user_id: str):
    """
    Удаление пользователя из БД
    """

    smth = select(UserDbEntity).options(selectinload(UserDbEntity.files)).where(UserDbEntity.id == user_id)

    with next(get_db()) as session:
        db_user = session.scalar(smth)

        if not db_user:
            return None

        session.delete(db_user)
        session.commit()

        return db_user


def get_user_by_username(username: str) -> Optional[UserBaseDto]:
    """
    Получение информации о пользователе по его имени
    """
    smth = select(UserDbEntity).where(UserDbEntity.username == username)
    with next(get_db()) as session:
        found = session.scalar(smth)
        if found:
            return UserBaseDto(
                id=found.id,
                username=found.username,
                hashed_password=found.hashed_password,
            )
        return None

def get_user_by_id(user_id: str) -> Optional[UserBaseDto]:
    """
    Получение информации о пользователе по его id
    """
    smth = select(UserDbEntity).where(UserDbEntity.id == user_id)
    with next(get_db()) as session:
        found = session.scalar(smth)
        if found:
            return UserBaseDto(
                id=found.id,
                username=found.username,
                hashed_password=None,
            )
        return None


def create_user(user: UserCreateDto) -> UserBaseDto:
    """
    Создание нового пользователя
    """
    hashed_password = get_string_hash(user.password)
    db_user = UserDbEntity(username=user.username, hashed_password=hashed_password)
    with next(get_db()) as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserBaseDto.model_validate(db_user)


def get_all_users() -> List[UserBaseDto]:
    """
    Получение всех пользователей (использовать только для отладки)
    """
    smth = select(UserDbEntity)
    with next(get_db()) as session:
        return list(
            map(
                lambda db_entity: UserBaseDto.model_validate(db_entity),
                session.scalars(smth).all(),
            ),
        )

from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ._utils import Base, random_uuid


class UserDbEntity(Base):
    """
    Таблица с данными пользователей

    Attributes
    ----------
    __tablename__
        имя таблицы
    id
        уникальный идентификатор файла
    username
        имя пользователя
    hashed_password
        хэшированный пароль
    created_at
        время создания пользователя
    files
        файлы текущего пользователя
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=random_uuid)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Каскадное удаление файлов при удалении пользователя
    files: Mapped[List["FileDbEntity"]] = relationship(
        "FileDbEntity",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FileDbEntity(Base):
    """
    Таблица с файлами пользователей

    Attributes
    ----------
    __tablename__
        имя таблицы
    id
        уникальный идентификатор файла
    original_name
        имя файла. Представляет собой строку вида <path>/<relative-to_root_on_device>/filename.ext
        Используется для визуализации дерева файлов на устройстве пользователя.
        Формируется исходя из иерархии файлов, которая загружается на сервер. Не имеет никакого отношения к
        структуре файлов в MinIO
    minio_object_name
        имя файла в MinIO. Представляет собой строку вида <MinIO_user>/file.ext
        Формируется при загрузке в MinIO и не имеет никакого отношения к иерархии файлов внутри архивов.
    size_bytes
        размер файла в байтах
    mime_type
        mime тип файла
    created_at
        время создания файла
    owner_id
        id пользователя, который загрузил файл
    owner
        ссылка на модель овнера. Связь только для каскадного удаления, без необходимости тянуть весь объект
    """

    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    minio_object_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    track_title: Mapped[str] = mapped_column(String, nullable=True)
    track_number: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    album: Mapped[str] = mapped_column(String, nullable=True)
    artist: Mapped[str] = mapped_column(String, nullable=True)
    genre: Mapped[str] = mapped_column(String, nullable=True)
    cover: Mapped[str] = mapped_column(String, nullable=True)

    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    owner: Mapped["UserDbEntity"] = relationship(back_populates="files")

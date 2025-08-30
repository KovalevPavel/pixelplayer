from typing import List

from sqlalchemy import select

from app.db.database import get_db

from ...db.db_dto import FileDbDto
from .file_dto import FileCreateDto, FileWithHierarchyDto


def get_all_files() -> List[FileDbDto]:
    """
    Получение всех файлов (только для отладки)
    """
    smth = select(FileDbDto)
    with next(get_db()) as session:
        return session.scalars(smth).all()


def get_file(file_id: str) -> FileDbDto | None:
    """
    Получение метаданных файла из БД
    """
    smth = select(FileDbDto).where(FileDbDto.id == file_id)
    with next(get_db()) as session:
        return session.scalar(smth)


def get_files_by_owner(owner_id: str, skip: int = 0, limit: int = 100, search: str = None) -> List[FileDbDto]:
    """
    Получение метаданных всех файлов, принадлежащих пользователю
    """
    smth = select(FileDbDto).where(FileDbDto.owner_id == owner_id)
    if search:
        smth = smth.where(FileDbDto.original_name.ilike(f"%{search}%"))
    with next(get_db()) as session:
        return session.scalars(smth.offset(skip).limit(limit)).all()


def create_file(file: FileCreateDto, owner_id: str):
    """
    Создание метаданных нового файла в БД
    """

    db_file = FileDbDto(**file.model_dump(), owner_id=owner_id)
    with next(get_db()) as session:
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
    return db_file


def delete_file(file_id: str):
    """
    Удаление метаданных файла из БД
    """
    db_file = get_file(file_id)
    if db_file:
        with next(get_db()) as session:
            session.delete(db_file)
            session.commit()
    return db_file


def get_files_json(user_id: str) -> List[FileWithHierarchyDto]:
    files = get_files_by_owner(owner_id=user_id)
    result = list(
        map(
            lambda file: __map_to_file_with_hierarchy(file),
            files,
        )
    )
    return result


def __map_to_file_with_hierarchy(file: FileDbDto) -> FileWithHierarchyDto:
    return FileWithHierarchyDto(
        id=file.id,
        original_name=file.original_name,
        size_bytes=file.size_bytes,
        mime_type=file.mime_type,
        minio_object_name=file.minio_object_name,
    )

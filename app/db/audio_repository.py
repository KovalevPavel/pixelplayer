from typing import List

from sqlalchemy import select

from ..core.models.file_dto import CoverInDto, FileCreateDto
from ._database import get_db
from ._entities import AudioFileDbEntity, CoverFileDbEntity


def get_all_files() -> List[AudioFileDbEntity]:
    """
    Получение всех файлов (только для отладки)
    """
    smth = select(AudioFileDbEntity)
    with next(get_db()) as session:
        return session.scalars(smth).all()


def get_file(file_id: str) -> AudioFileDbEntity | None:
    """
    Получение метаданных файла из БД
    """
    smth = select(AudioFileDbEntity).where(AudioFileDbEntity.id == file_id)
    with next(get_db()) as session:
        return session.scalar(smth)


def get_files_by_owner(owner_id: str, skip: int = 0, limit: int = 100, search: str = None) -> List[AudioFileDbEntity]:
    """
    Получение метаданных всех файлов, принадлежащих пользователю
    """
    smth = select(AudioFileDbEntity).where(AudioFileDbEntity.owner_id == owner_id)
    if search:
        smth = smth.where(AudioFileDbEntity.original_name.ilike(f"%{search}%"))
    with next(get_db()) as session:
        return session.scalars(smth.offset(skip).limit(limit)).all()


def create_audio_file(file: FileCreateDto, owner_id: str):
    """
    Создание метаданных нового аудио файла в БД
    """

    db_file = AudioFileDbEntity(**file.model_dump(), owner_id=owner_id)
    with next(get_db()) as session:
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
    return db_file

def create_cover_file(file: CoverInDto):
    """
    Создание метаданных нового файла обложки в БД
    """
    
    db_file = CoverFileDbEntity(**file.model_dump())
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


# def get_files_json(self, user_id: str) -> List[FileWithHierarchyDto]:
#     files = get_files_by_owner(owner_id=user_id)
#     result = list(
#         map(
#             lambda file: __map_to_file_with_hierarchy(file),
#             files,
#         )
#     )
#     return result
#
# def __map_to_file_with_hierarchy(self, file: FileDbEntity) -> FileWithHierarchyDto:
#     return FileWithHierarchyDto(
#         id=file.id,
#         original_name=file.original_name,
#         size_bytes=file.size_bytes,
#         mime_type=file.mime_type,
#         minio_object_name=file.minio_object_name,
#     )

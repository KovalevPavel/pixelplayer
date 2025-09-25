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

def get_feature_awailability(owner_id: str) -> dict[str, bool]:
    albums_query = select(AudioFileDbEntity.album).where(AudioFileDbEntity.owner_id == owner_id)
    artists_query = select(AudioFileDbEntity.artist).where(AudioFileDbEntity.owner_id == owner_id)
    genres_query = select(AudioFileDbEntity.genre).where(AudioFileDbEntity.owner_id == owner_id)

    tracks_exists = False
    genres_exists = False
    albums_exists = False
    artists_exists = False

    def __get_res():
        return {
            "tracks": tracks_exists,
            "genres": genres_exists,
            "albums": albums_exists,
            "artists": artists_exists,
        }

    with next(get_db()) as session:
        is_at_least_one_track_exists = (
            True
            if session.query(AudioFileDbEntity)
            .where(AudioFileDbEntity.owner_id == owner_id)
            .first()
            else False
        )
        if not is_at_least_one_track_exists:
            return __get_res()
        else:
            tracks_exists = True
 
        genres = [
            genre for genre in session.scalars(genres_query).unique()
            if genre
        ]
        if len(genres) > 0:
            genres_exists = True

        albums = [
            genre for genre in session.scalars(albums_query).unique()
            if genre
        ]
        if len(albums) > 0:
            albums_exists = True

        artists = [
            genre for genre in session.scalars(artists_query).unique()
            if genre
        ]
        if len(artists) > 0:
            artists_exists = True

        return __get_res()

def get_genres(owner_id: str) -> List[str]:
    smth = select(AudioFileDbEntity.genre).where(AudioFileDbEntity.owner_id == owner_id)
    with next(get_db()) as session:
        return [genre for genre in session.scalars(smth).unique() if genre]

def get_albums(owner_id: str) -> List[str]:
    smth = select(AudioFileDbEntity.album).where(AudioFileDbEntity.owner_id == owner_id)
    with next(get_db()) as session:
        return session.scalars(smth).unique()

def get_artists(owner_id: str) -> List[str]:
    smth = select(AudioFileDbEntity.artist).where(AudioFileDbEntity.owner_id == owner_id)
    with next(get_db()) as session:
        return session.scalars(smth).unique()

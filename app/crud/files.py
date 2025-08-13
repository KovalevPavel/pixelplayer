from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import models, schemas

def get_file(db: Session, file_id: int) -> models.File | None:
    smth = select(models.File).where(models.File.id == file_id)
    with db:
        return db.scalars(smth).first()

def get_files_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100, search: str = None):
    smth = select(models.File).where(models.File.owner_id == owner_id)
    if search:
        smth = smth.where(models.File.original_name.ilike(f"%{search}%"))
    with db:
        return db.scalars(smth.offset(skip).limit(limit)).all()

def create_file(db: Session, file: schemas.FileCreate, owner_id: int):
    db_file = models.File(**file.model_dump(), owner_id=owner_id)
    with db:
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

def delete_file(db: Session, file_id: int):
    db_file = get_file(db, file_id)
    if db_file:
        with db:
            db.delete(db_file)
            db.commit()
    return db_file

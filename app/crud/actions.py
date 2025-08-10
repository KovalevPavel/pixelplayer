from sqlalchemy.orm import Session
from .. import models, schemas
from ..core.security import get_password_hash, verify_password

# --- User CRUD ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
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

# --- File CRUD ---

def get_file(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()

def get_files_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.File).filter(models.File.owner_id == owner_id)
    if search:
        query = query.filter(models.File.original_name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def create_file(db: Session, file: schemas.FileCreate, owner_id: int):
    db_file = models.File(**file.dict(), owner_id=owner_id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int):
    db_file = get_file(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
    return db_file

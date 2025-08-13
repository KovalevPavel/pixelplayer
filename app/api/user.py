from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from typing import List
from .. import crud
from ..db import schemas
from ..core.security import create_access_token, get_current_active_user
from ..db.database import get_db

authRouter = APIRouter(
    prefix="/user"
)

@authRouter.post("/auth", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Авторизация пользователя"""
    # В FastAPI form_data приходит из `application/x-www-form-urlencoded`
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@authRouter.post("/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
Создает пользователя
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@authRouter.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    crud.delete_user(db, current_user.id)

@authRouter.get("/list", response_model=List[schemas.User])
def list_users(
        db: Session = Depends(get_db),
):
    return crud.get_all_users(db)

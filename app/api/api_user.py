from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db import audio_repository

from ..authorization import auth_repository
from ..authorization.token_dto import TokenDto
from ..core.models.user_dto import UserBaseDto, UserCreateDto, UserWithFilesDto
from ..db import user_repository
from ..minio import minio_repository

authRouter = APIRouter(prefix="/user")


@authRouter.post("/auth", response_model=TokenDto)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Авторизация пользователя
    """
    # В FastAPI form_data приходит из `application/x-www-form-urlencoded`
    user = auth_repository.try_authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_repository.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@authRouter.post("/register", response_model=UserBaseDto)
def create_user(user: UserCreateDto):
    """
    Создает пользователя
    """
    db_user = user_repository.get_user_by_username(username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_repository.create_user(user=user)


@authRouter.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
):
    deleted_user = user_repository.delete_user(user_id=current_user.id)
    minio_repository.remove_files_by_user(username=deleted_user.username)


@authRouter.get("/me", response_model=UserWithFilesDto)
def get_full_user_data(
    current_user: UserBaseDto = Depends(auth_repository.get_current_active_user),
):
    return UserWithFilesDto(
        id=current_user.id,
        username=current_user.username,
        features=audio_repository.get_feature_awailability(owner_id=current_user.id),
    )


@authRouter.get("/list", response_model=List[UserBaseDto])
def list_users():
    return user_repository.get_all_users()

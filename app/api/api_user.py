from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..data.auth import auth_repository, token_dto
from ..data.file import file_repository
from ..data.user import user_dto, user_repository
from ..data.user.user_dto import UserBaseDto, UserCreateDto, UserWithFilesDto
from ..db.db_dto import UserDbDto

authRouter = APIRouter(prefix="/user")


@authRouter.post("/auth", response_model=token_dto.TokenDto)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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


@authRouter.post("/register", response_model=user_dto.UserBaseDto)
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
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
):
    user_repository.delete_user(user_id=current_user.id)


@authRouter.get("/me", response_model=UserWithFilesDto)
def get_full_user_data(
    current_user: UserDbDto = Depends(auth_repository.get_current_active_user),
):
    user = user_repository.get_user_by_username(username=current_user.username)
    user = UserBaseDto.model_validate(user)
    files = file_repository.get_files_json(user.id)
    return UserWithFilesDto(id=user.id, username=user.username, files=files)


@authRouter.get("/list", response_model=List[user_dto.UserBaseDto])
def list_users():
    return user_repository.get_all_users()

from fastapi import APIRouter, status

dirsRouter = APIRouter(prefix="/dirs")

@dirsRouter.post("/create", status_code=status.HTTP_200_OK)
def create_dir(
        new_dir: str,
        # current_user: schemas.User = Depends(get_current_active_user),
        # db: Session = Depends(get_db)
):
    return {"new": f"{new_dir}"}

@dirsRouter.put("/rename", status_code=status.HTTP_200_OK)
def rename_dir(
        old_name: str,
        new_name: str,
        # current_user: schemas.User = Depends(get_current_active_user),
        # db: Session = Depends(get_db),
):
    """Переименовывает директорию"""
    return {"old": f"{old_name}", "new": f"{new_name}"}

@dirsRouter.delete("/remove", status_code=status.HTTP_200_OK)
def remove_dir(
        dir_to_remove: str,
        # current_user: schemas.User = Depends(get_current_active_user),
        # db: Session = Depends(get_db),
):
    """Удаляет директорию и все её содержимое"""
    return {"deleted": f"{dir_to_remove}"}

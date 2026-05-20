from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser, get_current_superuser
from database_pkg.models.user import UserRead, UserUpdate, User
from app.services.platform.user import user_service
from app.services.platform.cloudinary_service import cloudinary_service
from fastapi import UploadFile, File, HTTPException

router = APIRouter()


@router.get("/", response_model=List[UserRead])
def read_users(
    session: SessionDep,
    current_user: User = Depends(get_current_superuser),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users.
    """
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users


@router.get("/me", response_model=UserRead)
def read_user_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_user_me(session: SessionDep, current_user: CurrentUser, user_in: UserUpdate):
    current_user = user_service.update(session, db_user=current_user, user_in=user_in)
    return current_user


@router.post("/me/picture", response_model=UserRead)
async def upload_profile_picture(
    session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image size must be less than 5MB")

    url = cloudinary_service.upload_image(file_bytes, current_user.id)

    # Update the user record
    user_in = UserUpdate(profile_picture_url=url)
    current_user = user_service.update(session, db_user=current_user, user_in=user_in)

    return current_user


@router.delete("/me/picture", response_model=UserRead)
def delete_profile_picture(session: SessionDep, current_user: CurrentUser):
    if current_user.profile_picture_url:
        cloudinary_service.delete_image(current_user.profile_picture_url)

        # Wait! To explicitly unset it in SQLModel/Pydantic when using update helpers, it's safer to pass a dict.
        current_user.profile_picture_url = None
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

    return current_user

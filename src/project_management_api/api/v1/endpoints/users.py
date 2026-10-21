import mimetypes
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.crud import user as crud_user
from project_management_api.crud.audit import create_audit_log
from project_management_api.db.session import get_db
from project_management_api.models.user import User
from project_management_api.schemas.dashboard import UserDashboardResponse
from project_management_api.schemas.user import UserResponse
from project_management_api.services.storage import StorageService

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Fetches the profile details of the currently authenticated user."""
    return current_user


@router.get(
    "/me/dashboard",
    response_model=UserDashboardResponse,
    summary="Get User Personal Dashboard Overview",
)
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches personal metrics, assigned tasks, and workspace summaries for the User Dashboard."""
    return crud_user.get_user_dashboard_data(db, user=current_user)


@router.put(
    "/me/avatar",
    response_model=UserResponse,
    summary="Upload or Replace Profile Avatar",
)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Uploads, validates, and sets the profile picture for the authenticated user."""
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Validate image format and limits
    mime_type, ext = StorageService.validate_avatar(content, file.filename or "avatar")

    # Remove previous avatar if one exists
    old_key = current_user.avatar_storage_key
    if old_key:
        StorageService.delete_file(old_key)

    # Save new avatar to storage
    new_key = StorageService.save_avatar(content, ext)
    current_user.avatar_storage_key = new_key

    create_audit_log(
        db,
        action="USER_AVATAR_UPDATED",
        resource_type="USER",
        resource_id=current_user.id,
        actor_id=current_user.id,
        details={"file_size": len(content), "mime_type": mime_type},
    )

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete(
    "/me/avatar",
    response_model=UserResponse,
    summary="Remove Profile Avatar",
)
def remove_user_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Removes the profile picture of the authenticated user and restores the default avatar."""
    if current_user.avatar_storage_key:
        StorageService.delete_file(current_user.avatar_storage_key)
        current_user.avatar_storage_key = None

        create_audit_log(
            db,
            action="USER_AVATAR_REMOVED",
            resource_type="USER",
            resource_id=current_user.id,
            actor_id=current_user.id,
            details={},
        )

        db.commit()
        db.refresh(current_user)

    return current_user


@router.get(
    "/{user_id}/avatar",
    summary="Retrieve User Profile Picture",
)
def get_user_avatar(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves and streams the avatar image for the specified user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.avatar_storage_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found for this user.",
        )

    file_path = StorageService.get_file_path(user.avatar_storage_key)
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "image/jpeg"

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )
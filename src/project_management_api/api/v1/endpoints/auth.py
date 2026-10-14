from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.crud import user as crud_user
from project_management_api.db.session import get_db
from project_management_api.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user account with unique email validation."""
    existing_user = crud_user.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    return crud_user.create_user(db, user_in=user_in)
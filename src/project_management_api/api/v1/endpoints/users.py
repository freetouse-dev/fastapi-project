from fastapi import APIRouter, Depends

from project_management_api.api.deps import get_current_user
from project_management_api.models.user import User
from project_management_api.schemas.user import UserResponse

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Fetches the profile details of the currently authenticated user."""
    return current_user
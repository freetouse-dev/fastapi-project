import jwt
from jwt.exceptions import InvalidTokenError
from collections.abc import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from project_management_api.config import get_settings
from project_management_api.crud import user as crud_user
from project_management_api.db.session import get_db
from project_management_api.models.user import User
from project_management_api.schemas.token import TokenPayload

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Decodes JWT token, validates user existence, and ensures account is active."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except InvalidTokenError:
        raise credentials_exception

    user = crud_user.get_user_by_id(db, user_id=int(token_data.sub))
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account.",
        )

    return user


def get_current_user_from_token_or_param(
    db: Session = Depends(get_db),
    header_token: str | None = Depends(oauth2_scheme_optional),
    param_token: str | None = None,
) -> User:
    """Authenticates user either from Authorization Bearer header or query param token (useful for file preview/downloads)."""
    token = header_token or param_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_current_user(db=db, token=token)
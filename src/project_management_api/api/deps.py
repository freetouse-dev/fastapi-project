import jwt
from jwt.exceptions import InvalidTokenError
from collections.abc import Generator
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from project_management_api.config import get_settings
from project_management_api.crud import company as crud_company
from project_management_api.crud import user as crud_user
from project_management_api.db.session import get_db
from project_management_api.models.company import Company, CompanyMember, CompanyStatus
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


def get_current_active_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_company_slug: str | None = Header(None, alias="X-Company-Slug"),
    company_slug: str | None = None,
) -> tuple[Company, CompanyMember | None]:
    """
    Resolves the company context from the X-Company-Slug header or company_slug query param.
    If not specified, falls back to the user's primary active company membership.
    Verifies that the user is an active member or superuser.
    Returns (Company, CompanyMember | None).
    """
    slug = x_company_slug or company_slug
    if not slug:
        # Check if user has active companies
        user_companies = crud_company.get_companies_for_user(db, user_id=current_user.id)
        if user_companies:
            company, member = user_companies[0]
            return company, member
        if current_user.is_superuser:
            first_company = db.query(Company).filter(Company.deleted_at.is_(None)).first()
            if first_company:
                return first_company, None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-Slug header or company_slug parameter is required for tenant context.",
        )

    company = crud_company.get_company_by_slug(db, slug=slug)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if company.status == CompanyStatus.SUSPENDED and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account is suspended.",
        )

    membership = crud_company.get_company_member(db, company_id=company.id, user_id=current_user.id)
    if not membership:
        if current_user.is_superuser:
            return company, None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this company.",
        )

    if membership.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your membership in this company is not active.",
        )

    return company, membership


def get_optional_active_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_company_slug: str | None = Header(None, alias="X-Company-Slug"),
    company_slug: str | None = None,
) -> tuple[Company | None, CompanyMember | None]:
    """
    Optionally resolves company context if provided.
    """
    slug = x_company_slug or company_slug
    if not slug:
        return None, None
    return get_current_active_company(
        db=db,
        current_user=current_user,
        x_company_slug=x_company_slug,
        company_slug=company_slug,
    )
from sqlalchemy.orm import Session

from project_management_api.core.security import hash_password
from project_management_api.models.user import User
from project_management_api.schemas.user import UserCreate

def get_user_by_email(db: Session, email: str) -> User | None:
    """Finds a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Finds a user by primary key ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Creates a new user record with hashed password."""
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        is_active=user_in.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
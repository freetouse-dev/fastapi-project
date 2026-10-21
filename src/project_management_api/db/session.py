from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from project_management_api.config import get_settings

settings = get_settings()

def get_engine_kwargs(url: str) -> dict:
    kwargs = {
        "pool_pre_ping": True,
    }
    if "mysql" in url:
        kwargs["pool_recycle"] = 3600
    return kwargs

engine = create_engine(settings.database_url, **get_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
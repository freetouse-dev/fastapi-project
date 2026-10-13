from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=255)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128, description="Plaintext password (min 8 chars)")

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=2, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=128)
    is_active: bool | None = None

class UserResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
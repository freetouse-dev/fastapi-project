from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

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

class UserAdminUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    is_superuser: bool | None = None

class UserResponse(UserBase):
    id: int
    is_verified: bool = False
    is_superuser: bool = False
    avatar_storage_key: str | None = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if self.avatar_storage_key:
            return f"/api/v1/users/{self.id}/avatar"
        return None

    model_config = ConfigDict(from_attributes=True)
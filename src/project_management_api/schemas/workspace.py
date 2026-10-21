import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from project_management_api.models.workspace import WorkspaceRole
from project_management_api.schemas.user import UserResponse

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)

class WorkspaceCreate(WorkspaceBase):
    slug: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Optional custom slug (lowercase alphanumeric with hyphens)",
    )

class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)

class WorkspaceResponse(WorkspaceBase):
    id: int
    slug: str
    owner_id: int
    company_id: int | None = None
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkspaceMemberAdd(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER

class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceRole

class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: WorkspaceRole
    joined_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)
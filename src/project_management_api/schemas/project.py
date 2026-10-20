import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from project_management_api.models.project import ProjectRole, ProjectStatus
from project_management_api.schemas.user import UserResponse

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)

class ProjectCreate(ProjectBase):
    key: str = Field(..., min_length=2, max_length=10, description="Short uppercase code, e.g. 'PROJ'")

    @field_validator("key")
    @classmethod
    def validate_and_uppercase_key(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z0-9]{2,10}$", v):
            raise ValueError("Key must be 2-10 alphanumeric characters (e.g. 'PROJ', 'API').")
        return v

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: ProjectStatus | None = None

class ProjectResponse(ProjectBase):
    id: int
    workspace_id: int
    key: str
    status: ProjectStatus
    created_by_id: int
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberAdd(BaseModel):
    email: str
    role: ProjectRole = ProjectRole.CONTRIBUTOR

class ProjectMemberUpdate(BaseModel):
    role: ProjectRole

class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)
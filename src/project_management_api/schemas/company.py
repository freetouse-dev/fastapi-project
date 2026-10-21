from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from project_management_api.models.company import CompanyRole, CompanyStatus
from project_management_api.schemas.user import UserResponse


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class CompanyCreate(CompanyBase):
    slug: str | None = Field(None, min_length=2, max_length=100)


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class CompanyMemberResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    role: CompanyRole
    status: str
    can_create_workspace: bool = False
    joined_at: datetime
    created_at: datetime
    user: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyResponse(CompanyBase):
    id: int
    slug: str
    status: CompanyStatus
    owner_id: int
    created_by_id: int
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    members_count: int | None = None
    workspaces_count: int | None = None
    my_role: CompanyRole | None = None
    can_create_workspace: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyMemberRoleUpdate(BaseModel):
    role: CompanyRole


class CompanyMemberAdd(BaseModel):
    email: EmailStr
    role: CompanyRole = CompanyRole.MEMBER


class CompanyCreationRequestCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100)
    company_slug: str | None = Field(None, min_length=2, max_length=100)
    business_description: str | None = Field(None, max_length=500)


class CompanyCreationRequestResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    company_slug: str
    business_description: str | None = None
    status: str
    reviewed_by_id: int | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    requester: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyCreationRequestReview(BaseModel):
    approved: bool
    rejection_reason: str | None = Field(None, max_length=500)


class CompanyInvitationCreate(BaseModel):
    email: EmailStr
    role: CompanyRole = CompanyRole.MEMBER


class CompanyInvitationResponse(BaseModel):
    id: int
    company_id: int
    email: str
    role: CompanyRole
    status: str
    expires_at: datetime
    created_at: datetime
    token: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyInvitationAccept(BaseModel):
    token: str

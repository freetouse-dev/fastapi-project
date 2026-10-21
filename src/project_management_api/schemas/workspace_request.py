from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from project_management_api.models.workspace import (
    WorkspaceAccessRequestStatus,
    WorkspaceAccessRequestType,
)
from project_management_api.schemas.user import UserResponse
from project_management_api.schemas.workspace import WorkspaceResponse


class WorkspaceAccessRequestCreate(BaseModel):
    request_type: WorkspaceAccessRequestType = WorkspaceAccessRequestType.CREATE_WORKSPACE
    workspace_id: int | None = None
    requested_role: str | None = None
    reason: str | None = Field(None, max_length=500)


class WorkspaceAccessRequestReview(BaseModel):
    decision_reason: str | None = Field(None, max_length=500)
    approved_role: str | None = None


class WorkspaceAccessRequestResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    request_type: WorkspaceAccessRequestType
    workspace_id: int | None = None
    requested_role: str | None = None
    reason: str | None = None
    status: WorkspaceAccessRequestStatus
    reviewer_id: int | None = None
    reviewed_at: datetime | None = None
    decision_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None
    workspace: WorkspaceResponse | None = None

    model_config = ConfigDict(from_attributes=True)

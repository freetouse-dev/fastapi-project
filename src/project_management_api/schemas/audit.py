from datetime import datetime
from pydantic import BaseModel, ConfigDict
from project_management_api.schemas.user import UserResponse


class AuditLogResponse(BaseModel):
    id: int
    actor_id: int | None = None
    action: str
    resource_type: str
    resource_id: str
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime
    actor: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    unverified_users: int
    total_companies: int = 0
    pending_company_requests: int = 0
    total_workspaces: int
    total_projects: int
    total_tasks: int
    total_comments: int
    total_audit_logs: int

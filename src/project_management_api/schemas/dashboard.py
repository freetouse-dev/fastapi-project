from pydantic import BaseModel, ConfigDict
from project_management_api.schemas.activity import TaskActivityResponse
from project_management_api.schemas.task import TaskResponse


class UserDashboardResponse(BaseModel):
    assigned_tasks: list[TaskResponse]
    total_assigned: int
    status_counts: dict[str, int]
    workspaces_count: int
    recent_activities: list[TaskActivityResponse]

    model_config = ConfigDict(from_attributes=True)

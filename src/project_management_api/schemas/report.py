from pydantic import BaseModel, ConfigDict
from project_management_api.models.task import TaskPriority, TaskStatus


class ProjectDashboardResponse(BaseModel):
    project_id: int
    project_key: str
    project_name: str
    total_tasks: int
    completed_tasks: int
    completion_rate_percentage: float
    overdue_tasks: int
    tasks_by_status: dict[TaskStatus, int]
    tasks_by_priority: dict[TaskPriority, int]

    model_config = ConfigDict(from_attributes=True)

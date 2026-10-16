from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from project_management_api.models.task import TaskPriority, TaskStatus
from project_management_api.schemas.user import UserResponse

class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None

class TaskCreate(TaskBase):
    assignee_email: EmailStr | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_email: EmailStr | None = None
    due_date: datetime | None = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    task_number: int
    ticket_key: str
    creator_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    creator: UserResponse
    assignee: UserResponse | None

    model_config = ConfigDict(from_attributes=True)
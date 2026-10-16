from datetime import datetime
from pydantic import BaseModel, ConfigDict
from project_management_api.models.activity import ActivityAction
from project_management_api.schemas.user import UserResponse


class TaskActivityResponse(BaseModel):
    id: int
    task_id: int
    actor_id: int
    action: ActivityAction
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime
    actor: UserResponse

    model_config = ConfigDict(from_attributes=True)

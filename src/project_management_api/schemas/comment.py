from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from project_management_api.schemas.user import UserResponse

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Comment text or markdown")

class CommentCreate(CommentBase):
    pass

class CommentUpdate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    task_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse

    model_config = ConfigDict(from_attributes=True)
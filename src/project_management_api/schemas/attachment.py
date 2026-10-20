from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field

class CommentAttachmentResponse(BaseModel):
    id: int
    comment_id: int
    original_filename: str
    mime_type: str
    file_size: int
    uploaded_by_id: int
    created_at: datetime

    @computed_field
    @property
    def download_url(self) -> str:
        return f"/api/v1/attachments/{self.id}/download"

    @computed_field
    @property
    def preview_url(self) -> str:
        return f"/api/v1/attachments/{self.id}/preview"

    model_config = ConfigDict(from_attributes=True)

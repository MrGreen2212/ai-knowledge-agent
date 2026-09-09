from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    object_name: str
    content_type: str | None = None
    size: int | None = None
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.media.models import MediaType, DisplayStyle


class MediaOut(BaseModel):
    id: uuid.UUID
    invitation_id: uuid.UUID
    media_type: MediaType
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    display_style: DisplayStyle
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}

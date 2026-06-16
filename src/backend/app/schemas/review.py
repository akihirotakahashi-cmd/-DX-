import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    municipality_name: str
    theme: str
    status: str
    created_at: datetime


class ReviewActionRequest(BaseModel):
    action: Literal["approved", "returned", "rejected"]
    comment: str | None = None

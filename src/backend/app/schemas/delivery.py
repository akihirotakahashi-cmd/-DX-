import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortalUrlRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: str
    issued_at: datetime
    sent_at: datetime | None
    portal_url: str  # computed field — set in router


class DeliveryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    municipality_name: str
    theme: str
    approved_at: datetime | None
    portal_issued: bool
    portal_sent: bool

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


UserRole = Literal["consultant", "tl", "manager", "system_admin"]


class UserCreate(BaseModel):
    tenant_id: uuid.UUID | None = None
    full_name: str
    email: EmailStr
    role: UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    full_name: str
    email: str
    role: str
    active: bool
    created_at: datetime
    updated_at: datetime

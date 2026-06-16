import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class TenantCreate(BaseModel):
    municipality_name: str
    tenant_code: str
    contract_start: date
    contract_end: date | None = None
    contact_email: EmailStr | None = None


class TenantUpdate(BaseModel):
    municipality_name: str | None = None
    contact_email: EmailStr | None = None
    status: str | None = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    municipality_name: str
    tenant_code: str
    status: str
    contract_start: date
    contract_end: date | None
    contact_email: str | None
    created_at: datetime
    updated_at: datetime

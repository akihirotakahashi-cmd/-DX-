import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_roles
from app.core.database import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantRead, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/", response_model=list[TenantRead])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_roles("system_admin", "manager")),
):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_roles("system_admin")),
):
    tenant = Tenant(
        municipality_name=body.municipality_name,
        tenant_code=body.tenant_code,
        contract_start=body.contract_start,
        contract_end=body.contract_end,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("system_admin", "manager", "consultant")),
):
    """担当者メール等を更新。consultant は自テナントのみ。"""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if current_user.role == "consultant" and str(current_user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("system_admin", "manager", "tl", "consultant")),
):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # consultant は自分のテナントのみ参照可能
    if current_user.role == "consultant" and str(current_user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return tenant

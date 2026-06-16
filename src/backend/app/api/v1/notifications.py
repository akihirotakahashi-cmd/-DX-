"""
システム内通知 (DEC-023)

GET   /api/v1/notifications          — 未読通知一覧
PATCH /api/v1/notifications/{id}/read — 個別既読
PATCH /api/v1/notifications/read-all  — 一括既読
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_roles
from app.core.database import get_db
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    message: str
    link_url: str | None
    read: bool
    created_at: datetime


@router.get("/", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager", "system_admin")),
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    if unread_only:
        stmt = stmt.where(Notification.read == False)  # noqa: E712
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager", "system_admin")),
):
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == current_user.user_id, Notification.read == False)  # noqa: E712
    )
    return {"count": result.scalar_one()}


@router.patch("/read-all", status_code=204)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager", "system_admin")),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.user_id, Notification.read == False)  # noqa: E712
        .values(read=True)
    )
    await db.commit()


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager", "system_admin")),
):
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(notif.user_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    notif.read = True
    await db.commit()

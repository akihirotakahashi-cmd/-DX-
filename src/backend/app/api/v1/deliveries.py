"""
F-03: 自治体納品フロー

POST /api/v1/proposals/{id}/portal-urls  — ポータル URL 発行 (冪等: DEC-003/DEC-021)
POST /api/v1/proposals/{id}/send         — SES メール送信 (冪等: DEC-008)
GET  /api/v1/proposals/{id}/delivery     — 納品準備情報 (SCR-11)
GET  /api/v1/deliveries                  — 納品状況一覧 (SCR-13)
"""
import secrets
import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.models.portal_url import PortalUrl
from app.models.proposal import Proposal
from app.models.tenant import Tenant
from app.schemas.delivery import DeliveryItem, PortalUrlRead

router = APIRouter(tags=["deliveries"])


def _ses_client():
    return boto3.client("ses", region_name=settings.SES_REGION)


# ---------------------------------------------------------------------------
# SCR-11 用: 納品準備情報
# ---------------------------------------------------------------------------
class DeliveryPrep(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    proposal_id: uuid.UUID
    municipality_name: str
    theme: str
    approved_at: datetime | None
    contact_email: str | None
    portal_token: str | None
    portal_url: str | None
    sent_at: datetime | None
    downloaded_at: datetime | None


@router.get("/proposals/{proposal_id}/delivery", response_model=DeliveryPrep)
async def get_delivery_prep(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "approved":
        raise HTTPException(status_code=409, detail="Proposal is not approved")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    tenant = await db.get(Tenant, proposal.tenant_id)
    portal_result = await db.execute(select(PortalUrl).where(PortalUrl.proposal_id == proposal_id))
    portal = portal_result.scalar_one_or_none()

    return DeliveryPrep(
        proposal_id=proposal.id,
        municipality_name=proposal.municipality_name,
        theme=proposal.theme,
        approved_at=proposal.approved_at,
        contact_email=tenant.contact_email if tenant else None,
        portal_token=portal.token if portal else None,
        portal_url=f"{settings.PORTAL_BASE_URL}/portal/{portal.token}" if portal else None,
        sent_at=portal.sent_at if portal else None,
        downloaded_at=portal.downloaded_at if portal else None,
    )


# ---------------------------------------------------------------------------
# ポータル URL 発行 (冪等: DEC-003/DEC-021)
# ---------------------------------------------------------------------------
@router.post(
    "/proposals/{proposal_id}/portal-urls",
    response_model=PortalUrlRead,
    status_code=status.HTTP_201_CREATED,
)
async def issue_portal_url(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "approved":
        raise HTTPException(status_code=409, detail="Proposal is not approved")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    existing = await db.execute(select(PortalUrl).where(PortalUrl.proposal_id == proposal_id))
    portal = existing.scalar_one_or_none()
    if portal:
        portal_read = PortalUrlRead.model_validate(portal)
        portal_read.portal_url = f"{settings.PORTAL_BASE_URL}/portal/{portal.token}"
        return portal_read

    token = secrets.token_hex(32)
    portal = PortalUrl(
        proposal_id=proposal_id,
        token=token,
        issued_by=current_user.user_id,
    )
    db.add(portal)
    await db.commit()
    await db.refresh(portal)

    portal_read = PortalUrlRead.model_validate(portal)
    portal_read.portal_url = f"{settings.PORTAL_BASE_URL}/portal/{portal.token}"
    return portal_read


# ---------------------------------------------------------------------------
# SES メール送信 (冪等: DEC-008)
# ---------------------------------------------------------------------------
@router.post("/proposals/{proposal_id}/send", status_code=status.HTTP_204_NO_CONTENT)
async def send_portal_email(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if str(proposal.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await db.execute(select(PortalUrl).where(PortalUrl.proposal_id == proposal_id))
    portal = result.scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=404, detail="Portal URL not issued yet")

    if portal.sent_at:
        return  # 冪等: 送信済み

    tenant = await db.get(Tenant, proposal.tenant_id)
    if not tenant or not tenant.contact_email:
        raise HTTPException(status_code=422, detail="Tenant contact email is not configured")

    portal_url = f"{settings.PORTAL_BASE_URL}/portal/{portal.token}"
    ses = _ses_client()
    ses.send_email(
        Source=settings.SES_FROM_EMAIL,
        Destination={"ToAddresses": [tenant.contact_email]},
        Message={
            "Subject": {"Data": f"【地方創生DX】{proposal.municipality_name} 様 提案書ポータルのご案内"},
            "Body": {
                "Text": {
                    "Data": (
                        f"{proposal.municipality_name} 担当者様\n\n"
                        f"このたびは「{proposal.theme}」に関する提案書が承認されました。\n"
                        "以下のURLよりご確認いただけます。\n\n"
                        f"ポータルURL: {portal_url}\n\n"
                        "本URLは失効しませんので、大切に保管してください。\n\n"
                        "ご不明な点は担当コンサルタントまでお問い合わせください。"
                    )
                }
            },
        },
    )
    portal.sent_at = datetime.now(timezone.utc)
    await db.commit()


# ---------------------------------------------------------------------------
# 納品状況一覧 (SCR-13)
# ---------------------------------------------------------------------------
@router.get("/deliveries", response_model=list[DeliveryItem])
async def list_deliveries(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("consultant", "tl", "manager")),
):
    stmt = (
        select(Proposal)
        .where(Proposal.status == "approved")
        .order_by(Proposal.approved_at.desc())
    )
    if current_user.role == "consultant" and current_user.tenant_id:
        stmt = stmt.where(Proposal.tenant_id == current_user.tenant_id)

    result = await db.execute(stmt)
    proposals = result.scalars().all()

    items = []
    for p in proposals:
        portal_result = await db.execute(select(PortalUrl).where(PortalUrl.proposal_id == p.id))
        portal = portal_result.scalar_one_or_none()
        items.append(
            DeliveryItem(
                id=p.id,
                municipality_name=p.municipality_name,
                theme=p.theme,
                approved_at=p.approved_at,
                portal_issued=portal is not None,
                portal_sent=portal is not None and portal.sent_at is not None,
            )
        )
    return items

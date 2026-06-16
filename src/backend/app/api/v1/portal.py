"""
F-03: ポータル公開ページ API (認証不要 — DEC-021)

GET  /api/v1/portal/{token}          — 提案書メタデータ取得
POST /api/v1/portal/{token}/download — ダウンロード記録 (冪等: DEC-008)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.portal_url import PortalUrl
from app.models.proposal import Proposal

router = APIRouter(prefix="/portal", tags=["portal"])


class PortalProposalResponse(BaseModel):
    municipality_name: str
    theme: str
    content_url: str | None


@router.get("/{token}", response_model=PortalProposalResponse)
async def get_portal_proposal(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """認証不要 (DEC-021)。トークンで提案書メタを返す。"""
    result = await db.execute(select(PortalUrl).where(PortalUrl.token == token))
    portal = result.scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=404, detail="Portal URL not found")

    proposal = await db.get(Proposal, portal.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return PortalProposalResponse(
        municipality_name=proposal.municipality_name,
        theme=proposal.theme,
        content_url=proposal.content_url,
    )


@router.post("/{token}/download", status_code=204)
async def record_download(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """ダウンロード日時を記録 (冪等: DEC-008)。"""
    result = await db.execute(select(PortalUrl).where(PortalUrl.token == token))
    portal = result.scalar_one_or_none()
    if not portal:
        raise HTTPException(status_code=404, detail="Portal URL not found")

    if not portal.downloaded_at:
        portal.downloaded_at = datetime.now(timezone.utc)
        await db.commit()

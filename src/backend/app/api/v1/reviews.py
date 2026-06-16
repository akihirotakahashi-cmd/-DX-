"""
F-02: 承認フロー

GET  /api/v1/reviews            — TL/Mgr 向けレビュー待ち一覧 (DEC-024: ロールはトークンから判定)
GET  /api/v1/reviews/{id}       — レビュー詳細（提案書 + 承認履歴）
POST /api/v1/reviews/{id}       — 承認 / 差し戻し / 却下
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUser, require_roles
from app.core.database import get_db
from app.models.approval_step import ApprovalStep
from app.models.notification import Notification
from app.models.proposal import Proposal
from app.schemas.review import ReviewActionRequest, ReviewItem

router = APIRouter(prefix="/reviews", tags=["reviews"])

_ROLE_STATUS = {
    "tl": "reviewing_tl",
    "manager": "reviewing_mgr",
}
_NEXT_STATUS = {
    ("tl", "approved"): "reviewing_mgr",
    ("tl", "returned"): "draft",
    ("tl", "rejected"): "rejected",
    ("manager", "approved"): "approved",
    ("manager", "returned"): "reviewing_tl",
    ("manager", "rejected"): "rejected",
}
_STEP_NUMBER = {"tl": 1, "manager": 2}

_ACTION_LABEL = {
    "submitted": "提出",
    "approved": "承認",
    "returned": "差し戻し",
    "rejected": "却下",
}


class ApprovalStepItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    action: str
    comment: str | None
    executed_at: datetime


class ReviewDetail(ReviewItem):
    content_url: str | None
    parent_proposal_id: uuid.UUID | None
    steps: list[ApprovalStepItem] = []


# ---------------------------------------------------------------------------
# レビュー待ち一覧 (DEC-024)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ReviewItem])
async def list_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("tl", "manager")),
):
    target_status = _ROLE_STATUS[current_user.role]
    result = await db.execute(
        select(Proposal)
        .where(Proposal.status == target_status)
        .order_by(Proposal.updated_at.asc())
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# レビュー詳細
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}", response_model=ReviewDetail)
async def get_review(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("tl", "manager")),
):
    proposal = await db.get(
        Proposal,
        proposal_id,
        options=[selectinload(Proposal.approval_steps)],
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return ReviewDetail(
        id=proposal.id,
        municipality_name=proposal.municipality_name,
        theme=proposal.theme,
        status=proposal.status,
        created_at=proposal.created_at,
        content_url=proposal.content_url,
        parent_proposal_id=proposal.parent_proposal_id,
        steps=[
            ApprovalStepItem(
                id=s.id,
                step_number=s.step_number,
                action=s.action,
                comment=s.comment,
                executed_at=s.executed_at,
            )
            for s in sorted(proposal.approval_steps, key=lambda s: s.executed_at)
        ],
    )


# ---------------------------------------------------------------------------
# 承認アクション
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}", response_model=ReviewItem)
async def act_on_review(
    proposal_id: uuid.UUID,
    body: ReviewActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("tl", "manager")),
):
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    expected_status = _ROLE_STATUS[current_user.role]
    if proposal.status != expected_status:
        raise HTTPException(status_code=409, detail="Proposal is not in expected review status")

    next_status = _NEXT_STATUS[(current_user.role, body.action)]

    step = ApprovalStep(
        proposal_id=proposal.id,
        step_number=_STEP_NUMBER[current_user.role],
        actor_id=current_user.user_id,
        action=body.action,
        comment=body.comment,
    )
    db.add(step)

    proposal.status = next_status
    if next_status == "approved":
        proposal.approved_at = datetime.now(timezone.utc)

    # システム内通知 (DEC-023) — コンサルタントへ
    label = _ACTION_LABEL.get(body.action, body.action)
    notif = Notification(
        user_id=proposal.created_by,
        type=f"proposal_{body.action}",
        message=f"提案「{proposal.theme}」が{label}されました。",
        link_url=f"/proposals/{proposal.id}",
    )
    db.add(notif)

    await db.commit()
    await db.refresh(proposal)
    return proposal

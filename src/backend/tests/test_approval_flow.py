"""
F-02 承認フロー 統合テスト

TL承認 → MGR承認 → approved の完全フローを検証。
DEC-024: GET /reviews のロール判定をトークンから行う。
DEC-023: 承認アクション後に通知が作成される。
"""
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.proposal import Proposal
from app.models.tenant import Tenant
from app.models.user import User


async def _make_reviewing_tl_proposal(
    db: AsyncSession,
    tenant_id: str,
    consultant_user_id: str,
    reviewer_user_ids: list[tuple[str, str]] | None = None,
) -> str:
    """reviewing_tl 状態の提案を DB に直接作成する。
    reviewer_user_ids: [(user_id, role), ...] - FK を通すためのレビュアーユーザー
    """
    tenant = Tenant(
        id=uuid.UUID(tenant_id),
        municipality_name="承認テスト市",
        tenant_code=f"appr-{tenant_id[:8]}",
        contract_start=date(2026, 1, 1),
    )
    db.add(tenant)

    consultant = User(
        id=uuid.UUID(consultant_user_id),
        tenant_id=uuid.UUID(tenant_id),
        full_name="承認テストコンサル",
        email=f"c-{consultant_user_id[:8]}@test.example.com",
        role="consultant",
    )
    db.add(consultant)

    if reviewer_user_ids:
        for uid, role in reviewer_user_ids:
            reviewer = User(
                id=uuid.UUID(uid),
                tenant_id=None,
                full_name=f"{role.upper()} テストユーザー",
                email=f"{role}-{uid[:8]}@test.example.com",
                role=role,
            )
            db.add(reviewer)

    proposal = Proposal(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        created_by=uuid.UUID(consultant_user_id),
        municipality_name="承認テスト市",
        theme="承認フローテスト",
        status="reviewing_tl",
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return str(proposal.id)


@pytest.mark.asyncio
async def test_tl_approves_moves_to_reviewing_mgr(
    tl_client: AsyncClient, db: AsyncSession
):
    """TL が承認すると reviewing_mgr になる。"""
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())
    proposal_id = await _make_reviewing_tl_proposal(
        db, tenant_id, consultant_id,
        reviewer_user_ids=[(tl_client.user_id, "tl")],
    )

    res = await tl_client.post(
        f"/api/v1/reviews/{proposal_id}",
        json={"action": "approved", "comment": "問題なし"},
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "reviewing_mgr"


@pytest.mark.asyncio
async def test_tl_returns_moves_to_draft(tl_client: AsyncClient, db: AsyncSession):
    """TL が差し戻すと draft に戻る。"""
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())
    proposal_id = await _make_reviewing_tl_proposal(
        db, tenant_id, consultant_id,
        reviewer_user_ids=[(tl_client.user_id, "tl")],
    )

    res = await tl_client.post(
        f"/api/v1/reviews/{proposal_id}",
        json={"action": "returned", "comment": "修正が必要です"},
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_full_approval_flow(db: AsyncSession):
    """TL承認 → MGR承認 → approved の完全フロー。
    tl_client と manager_client を同時に使うと app.dependency_overrides が競合するため、
    1つの AsyncClient で override を切り替えながらテストする。
    """
    from httpx import ASGITransport, AsyncClient as _AsyncClient
    from app.core.auth import verify_token as _verify_token
    from app.core.database import get_db as _get_db
    from app.main import app as _app

    tl_id = str(uuid.uuid4())
    mgr_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())

    proposal_id = await _make_reviewing_tl_proposal(
        db, tenant_id, consultant_id,
        reviewer_user_ids=[(tl_id, "tl"), (mgr_id, "manager")],
    )

    tl_claims = {"sub": tl_id, "email": "tl@test.example.com", "custom:role": "tl", "custom:tenant_id": None, "client_id": "test-client"}
    mgr_claims = {"sub": mgr_id, "email": "mgr@test.example.com", "custom:role": "manager", "custom:tenant_id": None, "client_id": "test-client"}

    def db_dep():
        return db

    _app.dependency_overrides[_get_db] = db_dep

    async with _AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        # Step 1: TL 承認
        _app.dependency_overrides[_verify_token] = lambda: tl_claims
        tl_res = await client.post(
            f"/api/v1/reviews/{proposal_id}",
            json={"action": "approved"},
            headers={"Authorization": "Bearer dummy"},
        )
        assert tl_res.json()["status"] == "reviewing_mgr"

        # Step 2: MGR 承認
        _app.dependency_overrides[_verify_token] = lambda: mgr_claims
        mgr_res = await client.post(
            f"/api/v1/reviews/{proposal_id}",
            json={"action": "approved", "comment": "承認します"},
            headers={"Authorization": "Bearer dummy"},
        )
        assert mgr_res.status_code == 200
        assert mgr_res.json()["status"] == "approved"

    _app.dependency_overrides.clear()

    # approved_at が設定されていること
    await db.refresh(await db.get(Proposal, uuid.UUID(proposal_id)))
    proposal = await db.get(Proposal, uuid.UUID(proposal_id))
    assert proposal is not None
    assert proposal.approved_at is not None


@pytest.mark.asyncio
async def test_approval_creates_notification(tl_client: AsyncClient, db: AsyncSession):
    """DEC-023: 承認アクション後にコンサルタントへ通知が作成される。"""
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())
    proposal_id = await _make_reviewing_tl_proposal(
        db, tenant_id, consultant_id,
        reviewer_user_ids=[(tl_client.user_id, "tl")],
    )

    await tl_client.post(
        f"/api/v1/reviews/{proposal_id}",
        json={"action": "approved"},
        headers={"Authorization": "Bearer dummy"},
    )

    result = await db.execute(
        select(Notification).where(
            Notification.user_id == uuid.UUID(consultant_id)
        )
    )
    notifications = result.scalars().all()
    assert len(notifications) == 1
    assert "承認" in notifications[0].message
    assert notifications[0].read is False


@pytest.mark.asyncio
async def test_dec024_role_determined_from_token(tl_client: AsyncClient, db: AsyncSession):
    """DEC-024: GET /reviews のステータスはトークンのロールから決まる（TL なら reviewing_tl のみ）。"""
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())

    # reviewing_tl の提案を作成
    await _make_reviewing_tl_proposal(db, tenant_id, consultant_id)

    res = await tl_client.get(
        "/api/v1/reviews/",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    # 全件 reviewing_tl のみ（TL には reviewing_mgr は見えない）
    for item in res.json():
        assert item["status"] == "reviewing_tl"


@pytest.mark.asyncio
async def test_wrong_turn_rejected(manager_client: AsyncClient, db: AsyncSession):
    """MGR が reviewing_tl の提案を操作しようとすると 409。"""
    tenant_id = str(uuid.uuid4())
    consultant_id = str(uuid.uuid4())
    proposal_id = await _make_reviewing_tl_proposal(db, tenant_id, consultant_id)
    # 提案は reviewing_tl 状態 → MGR の番ではない

    res = await manager_client.post(
        f"/api/v1/reviews/{proposal_id}",
        json={"action": "approved"},
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 409

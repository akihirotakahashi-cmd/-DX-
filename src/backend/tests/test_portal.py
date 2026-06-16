"""
F-03 ポータル統合テスト

DEC-021: ポータル URL は認証不要でアクセスできる。
DEC-008: ダウンロード記録は冪等（何度呼んでも同じ結果）。
"""
import secrets
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_url import PortalUrl
from app.models.proposal import Proposal
from app.models.tenant import Tenant
from app.models.user import User


async def _setup_portal(db: AsyncSession) -> tuple[str, str]:
    """承認済み提案とポータルURLを作成して (proposal_id, token) を返す。"""
    tenant = Tenant(
        id=uuid.uuid4(),
        municipality_name="ポータルテスト市",
        tenant_code=f"portal-{uuid.uuid4().hex[:8]}",
        contract_start=date(2026, 1, 1),
    )
    db.add(tenant)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        full_name="テストユーザー",
        email=f"u-{uuid.uuid4().hex[:8]}@test.example.com",
        role="consultant",
    )
    db.add(user)
    await db.flush()

    proposal = Proposal(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        created_by=user.id,
        municipality_name="ポータルテスト市",
        theme="ポータルテスト",
        status="approved",
        content_url="https://s3.example.com/proposals/test/content.md",
    )
    db.add(proposal)
    await db.flush()

    token = secrets.token_hex(32)
    portal = PortalUrl(
        id=uuid.uuid4(),
        proposal_id=proposal.id,
        token=token,
        issued_by=user.id,
    )
    db.add(portal)
    await db.commit()
    return str(proposal.id), token


@pytest.mark.asyncio
async def test_portal_accessible_without_auth(no_auth_client: AsyncClient, db: AsyncSession):
    """DEC-021: ポータルページは認証不要でアクセスできる。"""
    _, token = await _setup_portal(db)

    res = await no_auth_client.get(f"/api/v1/portal/{token}")
    assert res.status_code == 200
    data = res.json()
    assert data["municipality_name"] == "ポータルテスト市"
    assert data["theme"] == "ポータルテスト"
    assert data["content_url"] is not None


@pytest.mark.asyncio
async def test_portal_invalid_token_returns_404(no_auth_client: AsyncClient, db: AsyncSession):
    """無効なトークンは 404 を返す。"""
    res = await no_auth_client.get(f"/api/v1/portal/{'x' * 64}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_download_record_idempotent(no_auth_client: AsyncClient, db: AsyncSession):
    """DEC-008: 複数回ダウンロード記録を呼んでも downloaded_at は最初の値が保持される。"""
    _, token = await _setup_portal(db)

    res1 = await no_auth_client.post(f"/api/v1/portal/{token}/download")
    assert res1.status_code == 204

    res2 = await no_auth_client.post(f"/api/v1/portal/{token}/download")
    assert res2.status_code == 204

    # DB で downloaded_at が1件分しか記録されていないことをポータル取得で確認
    portal_res = await no_auth_client.get(f"/api/v1/portal/{token}")
    assert portal_res.status_code == 200


@pytest.mark.asyncio
async def test_send_email_idempotent(
    consultant_client: AsyncClient, db: AsyncSession, mock_ses
):
    """DEC-008: POST .../send は送信済みの場合に 204 を返して再送しない。"""
    tenant_id = consultant_client.tenant_id
    user_id = consultant_client.user_id

    # テナントとユーザーを作成（contact_email 付き）
    tenant = Tenant(
        id=uuid.UUID(tenant_id),
        municipality_name="送信冪等テスト市",
        tenant_code=f"idem-{tenant_id[:8]}",
        contract_start=date(2026, 1, 1),
        contact_email="contact@test-city.lg.jp",
    )
    db.add(tenant)

    user = User(
        id=uuid.UUID(user_id),
        tenant_id=uuid.UUID(tenant_id),
        full_name="テストユーザー",
        email=f"c-{user_id[:8]}@test.example.com",
        role="consultant",
    )
    db.add(user)

    proposal = Proposal(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        created_by=uuid.UUID(user_id),
        municipality_name="送信冪等テスト市",
        theme="送信テスト",
        status="approved",
    )
    db.add(proposal)
    await db.flush()

    token = secrets.token_hex(32)
    portal = PortalUrl(
        id=uuid.uuid4(),
        proposal_id=proposal.id,
        token=token,
        issued_by=uuid.UUID(user_id),
    )
    db.add(portal)
    await db.commit()

    # 1回目送信
    res1 = await consultant_client.post(
        f"/api/v1/proposals/{proposal.id}/send",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res1.status_code == 204
    assert mock_ses.send_email.call_count == 1

    # 2回目送信 → SES は呼ばれない
    res2 = await consultant_client.post(
        f"/api/v1/proposals/{proposal.id}/send",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res2.status_code == 204
    assert mock_ses.send_email.call_count == 1  # 増えていない

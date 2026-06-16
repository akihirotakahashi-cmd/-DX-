"""
F-03 納品フロー テスト

contact_email 未設定テナントへの送信は 422 を返すことを確認。
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


@pytest.mark.asyncio
async def test_send_requires_contact_email(consultant_client: AsyncClient, db: AsyncSession):
    """contact_email 未設定のテナントに送信しようとすると 422。"""
    tenant_id = uuid.UUID(consultant_client.tenant_id)
    user_id = uuid.UUID(consultant_client.user_id)

    # contact_email なしのテナントを作成
    tenant = Tenant(
        id=tenant_id,
        municipality_name="テスト市",
        tenant_code=f"nomail-{str(tenant_id)[:8]}",
        contract_start=date(2026, 1, 1),
        contact_email=None,
    )
    db.add(tenant)

    user = User(
        id=user_id,
        tenant_id=tenant_id,
        full_name="テストユーザー",
        email=f"c-{str(user_id)[:8]}@test.example.com",
        role="consultant",
    )
    db.add(user)

    proposal = Proposal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=user_id,
        municipality_name="テスト市",
        theme="DX推進",
        status="approved",
    )
    db.add(proposal)
    await db.flush()

    portal = PortalUrl(
        id=uuid.uuid4(),
        proposal_id=proposal.id,
        token=secrets.token_hex(32),
        issued_by=user_id,
    )
    db.add(portal)
    await db.commit()

    res = await consultant_client.post(
        f"/api/v1/proposals/{proposal.id}/send",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 422

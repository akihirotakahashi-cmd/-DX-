"""
F-01 施策提案フロー 統合テスト
"""
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User


async def _setup_tenant_user(db: AsyncSession, tenant_id: str, user_id: str) -> tuple[Tenant, User]:
    """テナントとユーザーを DB に作成して返す。"""
    tenant = Tenant(
        id=uuid.UUID(tenant_id),
        municipality_name="テスト市",
        tenant_code=f"test-{tenant_id[:8]}",
        contract_start=date(2026, 1, 1),
    )
    db.add(tenant)

    user = User(
        id=uuid.UUID(user_id),
        tenant_id=uuid.UUID(tenant_id),
        full_name="テストコンサル",
        email=f"consultant-{user_id[:8]}@test.example.com",
        role="consultant",
    )
    db.add(user)
    await db.commit()
    return tenant, user


@pytest.mark.asyncio
async def test_create_proposal(consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3):
    """提案書を生成できる。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    res = await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "高齢者向けデジタルデバイド解消"},
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["theme"] == "高齢者向けデジタルデバイド解消"
    assert data["municipality_name"] == "テスト市"
    assert data["content_url"] == "https://s3.example.com/proposals/test/content.md"


@pytest.mark.asyncio
async def test_get_proposal(consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3):
    """生成した提案書を詳細取得できる。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    create_res = await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "スマート農業推進"},
        headers={"Authorization": "Bearer dummy"},
    )
    proposal_id = create_res.json()["id"]

    res = await consultant_client.get(
        f"/api/v1/proposals/{proposal_id}",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == proposal_id
    assert "evidence" in data


@pytest.mark.asyncio
async def test_submit_proposal(consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3):
    """draft の提案を提出すると reviewing_tl になる。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    create_res = await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "観光DX推進"},
        headers={"Authorization": "Bearer dummy"},
    )
    proposal_id = create_res.json()["id"]

    res = await consultant_client.post(
        f"/api/v1/proposals/{proposal_id}/submit",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "reviewing_tl"


@pytest.mark.asyncio
async def test_submit_non_draft_fails(consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3):
    """draft 以外の提案を提出すると 409。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    create_res = await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "防災DX"},
        headers={"Authorization": "Bearer dummy"},
    )
    proposal_id = create_res.json()["id"]

    # 1回目提出
    await consultant_client.post(
        f"/api/v1/proposals/{proposal_id}/submit",
        headers={"Authorization": "Bearer dummy"},
    )
    # 2回目提出 → 409
    res = await consultant_client.post(
        f"/api/v1/proposals/{proposal_id}/submit",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_regenerate_supersedes_old(consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3):
    """DEC-022: 再生成は旧 draft を superseded にして新しい ID を返す。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    create_res = await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "元のテーマ"},
        headers={"Authorization": "Bearer dummy"},
    )
    old_id = create_res.json()["id"]

    regen_res = await consultant_client.post(
        f"/api/v1/proposals/{old_id}/regenerate",
        json={"theme": "改善テーマ"},
        headers={"Authorization": "Bearer dummy"},
    )
    assert regen_res.status_code == 201
    new_id = regen_res.json()["id"]
    assert new_id != old_id
    assert regen_res.json()["parent_proposal_id"] == old_id

    # 旧提案が superseded になっていること
    old_res = await consultant_client.get(
        f"/api/v1/proposals/{old_id}",
        headers={"Authorization": "Bearer dummy"},
    )
    assert old_res.json()["status"] == "superseded"


@pytest.mark.asyncio
async def test_list_proposals_scoped_to_tenant(
    consultant_client: AsyncClient, db: AsyncSession, mock_claude, mock_s3
):
    """consultant は自テナントの提案のみ参照できる。"""
    await _setup_tenant_user(db, consultant_client.tenant_id, consultant_client.user_id)

    await consultant_client.post(
        "/api/v1/proposals/",
        json={"theme": "テナントAの提案"},
        headers={"Authorization": "Bearer dummy"},
    )

    res = await consultant_client.get(
        "/api/v1/proposals/",
        headers={"Authorization": "Bearer dummy"},
    )
    assert res.status_code == 200
    # 全件が自テナントのもの
    for p in res.json():
        assert p["tenant_id"] == consultant_client.tenant_id

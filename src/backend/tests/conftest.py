"""
共通テストフィクスチャ

外部依存の差し替え方針:
  - JWT 検証  : verify_token を override → CurrentUser / require_roles が自然に動く
  - Claude API: services.claude.generate_proposal を patch
  - S3        : services.s3.upload_proposal_content を patch
  - SES       : boto3.client を patch
"""
import os
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.auth import verify_token
from app.main import app

# ---------------------------------------------------------------------------
# テスト DB
# ---------------------------------------------------------------------------
TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://chihousousei:password@localhost:5432/chihousousei_dx_test",
)


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """セッション全体で共有するエンジン。NullPool でループ間の接続共有を避ける。"""
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """テストごとのセッション。コンテキスト終了時にセッションをクローズする。"""
    TestSession = async_sessionmaker(db_engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session


# ---------------------------------------------------------------------------
# 認証ヘルパー
# ---------------------------------------------------------------------------
def make_claims(role: str, user_id: str | None = None, tenant_id: str | None = None) -> dict:
    return {
        "sub": user_id or str(uuid.uuid4()),
        "email": f"{role}@test.example.com",
        "custom:role": role,
        "custom:tenant_id": tenant_id,
        "client_id": "test-client",
    }


# ---------------------------------------------------------------------------
# HTTP クライアント (verify_token を差し替え)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def consultant_client(db: AsyncSession):
    """consultant ロールのクライアント"""
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    claims = make_claims("consultant", user_id=user_id, tenant_id=tenant_id)

    def override_db():
        return db

    def override_token():
        return claims

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[verify_token] = override_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.tenant_id = tenant_id  # type: ignore[attr-defined]
        client.user_id = user_id  # type: ignore[attr-defined]
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tl_client(db: AsyncSession):
    """TL ロールのクライアント"""
    user_id = str(uuid.uuid4())
    claims = make_claims("tl", user_id=user_id)

    def override_db():
        return db

    def override_token():
        return claims

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[verify_token] = override_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.user_id = user_id  # type: ignore[attr-defined]
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def manager_client(db: AsyncSession):
    """manager ロールのクライアント"""
    user_id = str(uuid.uuid4())
    claims = make_claims("manager", user_id=user_id)

    def override_db():
        return db

    def override_token():
        return claims

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[verify_token] = override_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.user_id = user_id  # type: ignore[attr-defined]
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def no_auth_client(db: AsyncSession):
    """認証不要エンドポイント用"""
    def override_db():
        return db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 外部サービスモック
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_claude():
    with patch(
        "app.api.v1.proposals.generate_proposal",
        new_callable=AsyncMock,
        return_value="# テスト提案書\n\n## エグゼクティブサマリー\nテスト用の提案書です。",
    ):
        yield


@pytest.fixture
def mock_s3():
    with patch(
        "app.api.v1.proposals.upload_proposal_content",
        return_value="https://s3.example.com/proposals/test/content.md",
    ):
        yield


@pytest.fixture
def mock_ses():
    mock = MagicMock()
    mock.send_email.return_value = {"MessageId": "test-message-id"}
    with patch("app.api.v1.deliveries.boto3.client", return_value=mock):
        yield mock

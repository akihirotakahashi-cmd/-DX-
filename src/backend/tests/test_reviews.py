"""
F-02 承認フロー テスト

DEC-024: GET /reviews でロールはトークンから自動判定されることを確認。
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_list_reviews_uses_role_from_token(tl_client: AsyncClient, db: AsyncSession):
    """DEC-024: TL トークンで /reviews にアクセスするとロール判定が自動で行われ 200 を返す。"""
    res = await tl_client.get("/api/v1/reviews/", headers={"Authorization": "Bearer dummy"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_list_reviews_forbidden_for_consultant(
    consultant_client: AsyncClient, db: AsyncSession
):
    """consultant ロールは /reviews にアクセスできない (403)。"""
    res = await consultant_client.get(
        "/api/v1/reviews/", headers={"Authorization": "Bearer dummy"}
    )
    assert res.status_code == 403

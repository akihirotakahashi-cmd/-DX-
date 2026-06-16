"""
AWS Cognito JWT 検証ミドルウェア (DEC-029)
Cognito User Pool の JWKS エンドポイントから公開鍵を取得し、
Bearer トークンを検証する。

APP_ENV=demo の場合は Cognito を使わずデモ固定ユーザーで認証する。
"""
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.core.config import settings

_jwks_cache: dict | None = None
bearer_scheme = HTTPBearer()

# デモモード固定ユーザー (APP_ENV=demo のみ使用)
_DEMO_USERS: dict[str, dict] = {
    "demo-consultant": {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "consultant@demo.jp",
        "custom:role": "consultant",
        "custom:tenant_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "client_id": "demo-client",
    },
    "demo-tl": {
        "sub": "22222222-2222-2222-2222-222222222222",
        "email": "tl@demo.jp",
        "custom:role": "tl",
        "custom:tenant_id": None,
        "client_id": "demo-client",
    },
    "demo-manager": {
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "manager@demo.jp",
        "custom:role": "manager",
        "custom:tenant_id": None,
        "client_id": "demo-client",
    },
}


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com"
        f"/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
    _jwks_cache = resp.json()
    return _jwks_cache


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials

    if settings.APP_ENV == "demo":
        return _DEMO_USERS.get(token, _DEMO_USERS["demo-consultant"])

    try:
        header = jwt.get_unverified_header(token)
        jwks = await _get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")
        public_key = jwk.construct(key)
        message, encoded_sig = token.rsplit(".", 1)
        decoded_sig = base64url_decode(encoded_sig.encode())
        if not public_key.verify(message.encode(), decoded_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature verification failed")
        claims = jwt.get_unverified_claims(token)
        if claims.get("client_id") != settings.COGNITO_CLIENT_ID:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
        return claims
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


class CurrentUser:
    """依存性注入用: JWT クレームから現在ユーザー情報を取得"""

    def __init__(self, claims: dict = Depends(verify_token)):
        self.user_id: str = claims["sub"]
        self.email: str = claims.get("email", "")
        self.role: str = claims.get("custom:role", "consultant")
        self.tenant_id: str | None = claims.get("custom:tenant_id")


def require_roles(*roles: str):
    """ロールベースアクセス制御デコレータ"""

    def dependency(current_user: CurrentUser = Depends(CurrentUser)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {roles}",
            )
        return current_user

    return dependency

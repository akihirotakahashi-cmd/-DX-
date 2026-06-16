"""
アプリケーション共通例外ハンドラ
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("DB integrity error: %s", exc.orig)
        detail = "Duplicate entry or constraint violation"
        # UNIQUE 制約違反のメッセージを安全に返す
        if exc.orig and "unique" in str(exc.orig).lower():
            detail = "The resource already exists (unique constraint)"
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.models import *  # noqa: F401,F403 — models must be imported before Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="地方創生DX API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if settings.APP_ENV in ("development", "demo") else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)

# ---- routers ----------------------------------------------------------------
from app.api.v1 import proposals, reviews, deliveries, portal, tenants, users, notifications  # noqa: E402

app.include_router(tenants.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(proposals.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(deliveries.router, prefix="/api/v1")
app.include_router(portal.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

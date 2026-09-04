"""
LedgerLens — FastAPI Application Entry Point
Configures CORS, mounts all route modules, and handles startup/shutdown.
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import create_tables

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup (dev only)."""
    settings = get_settings()
    if settings.environment == "development":
        await create_tables()
        log.info("database_ready", environment=settings.environment)
    yield
    log.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="LedgerLens API",
        description=(
            "Autonomous AI Finance Controller — "
            "reconciles multi-source financial records, investigates exceptions, "
            "auto-resolves what's safe, escalates what isn't."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ──────────────────────────────────────────────────────────────
    from backend.api.routes import (
        evaluate,
        exceptions,
        ingest,
        metrics,
        reconcile,
        controller,
    )

    app.include_router(ingest.router, prefix="/api", tags=["ingestion"])
    app.include_router(reconcile.router, prefix="/api", tags=["reconciliation"])
    app.include_router(exceptions.router, prefix="/api", tags=["exceptions"])
    app.include_router(evaluate.router, prefix="/api", tags=["evaluation"])
    app.include_router(metrics.router, prefix="/api", tags=["metrics"])
    app.include_router(controller.router, prefix="/api", tags=["controller"])

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": "ledgerlens"}

    return app


app = create_app()

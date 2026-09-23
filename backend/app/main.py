"""FastAPI application entry point for Ask My Docs API."""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import (
    analytics,
    collections,
    documents,
    evaluation,
    feedback,
    health,
    query,
)
from app.core.config import settings
from app.core.database import create_vector_extension, init_db
from app.core.logging import bind_request_id, clear_context, configure_logging

log = structlog.get_logger(__name__)


# --------------------------------------------------------------------------- #
# Rate limiter
# --------------------------------------------------------------------------- #

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Application lifespan: startup and shutdown logic."""
    configure_logging()
    log.info("startup.begin", app=settings.APP_NAME, version=settings.APP_VERSION)
    await create_vector_extension()
    await init_db()
    log.info("startup.complete")
    yield
    log.info("shutdown.begin")


# --------------------------------------------------------------------------- #
# App factory
# --------------------------------------------------------------------------- #

def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        description=(
            "Production-grade enterprise RAG API. "
            "Upload documents, query them with citations, track analytics."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------ #
    # Middleware
    # ------------------------------------------------------------------ #

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------ #
    # Rate limiting
    # ------------------------------------------------------------------ #

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ #
    # Request-ID / structured logging middleware
    # ------------------------------------------------------------------ #

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        bind_request_id(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_context()

    # ------------------------------------------------------------------ #
    # Exception handlers
    # ------------------------------------------------------------------ #

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException  # noqa: ARG001
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        log.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"},
        )

    # ------------------------------------------------------------------ #
    # Routers
    # ------------------------------------------------------------------ #

    API_PREFIX = "/api"

    app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
    app.include_router(documents.router, prefix=API_PREFIX, tags=["Documents"])
    app.include_router(query.router, prefix=API_PREFIX, tags=["Query"])
    app.include_router(collections.router, prefix=API_PREFIX, tags=["Collections"])
    app.include_router(evaluation.router, prefix=API_PREFIX, tags=["Evaluation"])
    app.include_router(analytics.router, prefix=API_PREFIX, tags=["Analytics"])
    app.include_router(feedback.router, prefix=API_PREFIX, tags=["Feedback"])

    return app


app = create_app()

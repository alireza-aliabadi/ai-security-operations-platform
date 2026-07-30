"""FastAPI application factory and uvicorn entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from aisoc.api.router import api_router
from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger, setup_logging
from aisoc.core.telemetry import instrument_app, setup_telemetry
from aisoc.db.base import Base
from aisoc.db.session import dispose_engine, get_engine, get_session_factory

logger = get_logger(__name__)


async def _create_tables() -> None:
    # Import models so metadata is populated
    from aisoc.db import models as _models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _run_seed(settings: Settings) -> None:
    from aisoc.db.seed import run_seed

    factory = get_session_factory()
    async with factory() as session:
        await run_seed(session, settings)


async def _ingest_knowledge_best_effort() -> None:
    try:
        from aisoc.rag.ingest import ingest_seed_knowledge

        result = await ingest_seed_knowledge()
        logger.info("startup_knowledge_ingest", ingested=result.get("ingested"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup_knowledge_ingest_failed", error=str(exc))


def _setup_rate_limit(app: FastAPI, settings: Settings) -> Any | None:
    if not settings.rate_limit_enabled:
        return None
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware
        from slowapi.util import get_remote_address

        limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)
        logger.info("rate_limit_enabled", default=settings.rate_limit_default)
        return limiter
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate_limit_unavailable", error=str(exc))
        return None


_REQUEST_COUNTER: Any | None = None


def _setup_metrics(app: FastAPI, settings: Settings) -> None:
    if not settings.prometheus_enabled:
        return
    global _REQUEST_COUNTER
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

        if _REQUEST_COUNTER is None:
            _REQUEST_COUNTER = Counter(
                "aisoc_http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status"],
            )
        request_count = _REQUEST_COUNTER
        app.state.prom_request_count = request_count

        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next: Any) -> Response:
            response = await call_next(request)
            endpoint = request.url.path
            request_count.labels(request.method, endpoint, str(response.status_code)).inc()
            return response

        @app.get("/metrics")
        async def metrics() -> Response:
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

        logger.info("prometheus_metrics_enabled")
    except Exception as exc:  # noqa: BLE001
        logger.warning("prometheus_unavailable", error=str(exc))

        @app.get("/metrics")
        async def metrics_fallback() -> PlainTextResponse:
            return PlainTextResponse("# prometheus client unavailable\n")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    setup_logging(debug=settings.debug)
    setup_telemetry(settings)
    logger.info("app_starting", env=settings.app_env)

    try:
        await _create_tables()
        await _run_seed(settings)
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup_db_failed", error=str(exc))

    # Bootstrap mock connectors into the registry
    try:
        from aisoc.connectors.registry import get_registry

        get_registry()  # ensures default mock connectors are registered
    except Exception as exc:  # noqa: BLE001
        logger.warning("connector_registry_init_failed", error=str(exc))

    await _ingest_knowledge_best_effort()
    yield
    await dispose_engine()
    logger.info("app_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _setup_rate_limit(app, settings)
    instrument_app(app)

    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "aisoc-api"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        checks: dict[str, str] = {"api": "ok"}
        status_code = 200
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["database"] = f"error: {exc}"
            status_code = 503
        return JSONResponse({"status": "ready" if status_code == 200 else "degraded", "checks": checks}, status_code=status_code)

    _setup_metrics(app, settings)
    return app


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "aisoc.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug and settings.app_env == "development",
    )


# Prefer factory mode: `uvicorn aisoc.main:create_app --factory`
# Module-level app kept for ASGI servers that expect an `app` attribute.
app = create_app()

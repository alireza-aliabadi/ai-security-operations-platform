"""Shared pytest fixtures — test settings, SQLite engine, AsyncClient."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

# Force test environment before importing application modules.
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long!!"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["DATABASE_URL_SYNC"] = "sqlite://"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["OTEL_ENABLED"] = "false"
os.environ["PROMETHEUS_ENABLED"] = "false"
os.environ["LLM_PRIMARY_API_KEY"] = ""
os.environ["CONNECTOR_MODE"] = "mock"
os.environ["ENCRYPTION_KEY"] = "0123456789abcdef0123456789abcdef"
os.environ["OIDC_ENABLED"] = "false"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw):  # type: ignore[no-untyped-def]
    return "JSON"


@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(_type, _compiler, **_kw):  # type: ignore[no-untyped-def]
    return "CHAR(36)"


from aisoc.core.config import Settings, get_settings  # noqa: E402
from aisoc.db.base import Base  # noqa: E402
from aisoc.db.seed import run_seed  # noqa: E402
from aisoc.db import session as db_session  # noqa: E402
from aisoc.main import create_app  # noqa: E402


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    get_settings.cache_clear()
    settings = Settings(
        app_env="test",
        secret_key="test-secret-key-at-least-32-characters-long!!",
        database_url="sqlite+aiosqlite://",
        database_url_sync="sqlite://",
        rate_limit_enabled=False,
        otel_enabled=False,
        prometheus_enabled=False,
        llm_primary_api_key="",
        connector_mode="mock",
        oidc_enabled=False,
        encryption_key="0123456789abcdef0123456789abcdef",
        seed_admin_email="admin@aisoc.local",
        seed_admin_password="ChangeMeAdmin123!",
        seed_analyst_email="analyst@aisoc.local",
        seed_analyst_password="ChangeMeAnalyst123!",
    )

    def _override() -> Settings:
        return settings

    monkeypatch.setattr("aisoc.core.config.get_settings", _override)
    monkeypatch.setattr("aisoc.db.session.get_settings", _override)
    monkeypatch.setattr("aisoc.api.deps.get_settings", _override)
    monkeypatch.setattr("aisoc.main.get_settings", _override)
    get_settings.cache_clear()
    return settings


@pytest_asyncio.fixture
async def app(test_settings: Settings, monkeypatch: pytest.MonkeyPatch):
    await db_session.dispose_engine()

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    db_session._engine = engine
    db_session._session_factory = factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await run_seed(session, test_settings)

    application = create_app(test_settings)

    # Avoid lifespan re-init / dispose fighting the shared StaticPool engine.
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(_app):  # type: ignore[no-untyped-def]
        yield

    application.router.lifespan_context = _noop_lifespan

    # Ensure deps resolve to our settings
    monkeypatch.setattr("aisoc.api.deps.get_settings_dep", lambda: test_settings)

    yield application

    await db_session.dispose_engine()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

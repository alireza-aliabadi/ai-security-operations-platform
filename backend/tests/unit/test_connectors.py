"""Unit tests for connector registry parallel search and Graylog health."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from aisoc.connectors.base import SearchQuery
from aisoc.connectors.graylog import GraylogConnector
from aisoc.connectors.registry import ConnectorRegistry, reset_registry


@pytest.mark.asyncio
async def test_parallel_search_returns_logs() -> None:
    registry = reset_registry()
    results = await registry.parallel_search(SearchQuery(query="bruteforce OR C2 OR malware", limit=50))
    assert results
    total = sum(len(events) for events in results.values())
    assert total > 0
    # At least one event should reference known narrative terms
    blob = " ".join(
        e.message for events in results.values() for e in events
    ).lower()
    assert any(token in blob for token in ("bruteforce", "c2", "failed logon", "185.220"))


@pytest.mark.asyncio
async def test_graylog_health_mock() -> None:
    connector = GraylogConnector()
    health = await connector.health()
    assert health["status"] == "ok"
    assert health["platform"] == "graylog"
    assert health["mode"] == "mock"
    assert health["event_count"] > 0


@pytest.mark.asyncio
async def test_parallel_search_isolates_failures() -> None:
    registry = ConnectorRegistry()
    good = GraylogConnector(name="good-graylog")
    bad = GraylogConnector(name="bad-graylog")
    registry.register(good)
    registry.register(bad)

    with patch.object(bad, "search", new=AsyncMock(side_effect=RuntimeError("boom"))):
        results = await registry.parallel_search(SearchQuery(query="auth", limit=10))

    assert "good-graylog" in results
    assert "bad-graylog" in results
    assert results["bad-graylog"] == []
    assert len(results["good-graylog"]) >= 0

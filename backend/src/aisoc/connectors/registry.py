"""Connector registry with parallel cross-platform search."""

from __future__ import annotations

import asyncio
from typing import Any

from aisoc.connectors.base import AggregateResult, LogConnector, LogEvent, SearchQuery, TimelineEvent
from aisoc.connectors.datadog import DatadogConnector
from aisoc.connectors.elasticsearch import ElasticsearchConnector
from aisoc.connectors.graylog import GraylogConnector
from aisoc.connectors.loki import LokiConnector
from aisoc.connectors.opensearch import OpenSearchConnector
from aisoc.connectors.splunk import SplunkConnector
from aisoc.core.config import get_settings
from aisoc.core.logging import get_logger

logger = get_logger(__name__)

PLATFORM_FACTORIES: dict[str, type] = {
    "graylog": GraylogConnector,
    "elasticsearch": ElasticsearchConnector,
    "loki": LokiConnector,
    "splunk": SplunkConnector,
    "opensearch": OpenSearchConnector,
    "datadog": DatadogConnector,
}


class ConnectorRegistry:
    """In-memory registry of active log connectors."""

    def __init__(self) -> None:
        self._connectors: dict[str, LogConnector] = {}

    def register(self, connector: LogConnector) -> None:
        self._connectors[connector.name] = connector

    def unregister(self, name: str) -> None:
        self._connectors.pop(name, None)

    def get(self, name: str) -> LogConnector | None:
        return self._connectors.get(name)

    def get_by_platform(self, platform: str) -> list[LogConnector]:
        return [c for c in self._connectors.values() if c.platform == platform]

    def list(self) -> list[LogConnector]:
        return list(self._connectors.values())

    def clear(self) -> None:
        self._connectors.clear()

    async def parallel_search(self, query: SearchQuery) -> dict[str, list[LogEvent]]:
        connectors = self._select(query.platforms)
        if not connectors:
            return {}

        async def _one(conn: LogConnector) -> tuple[str, list[LogEvent]]:
            try:
                events = await conn.search(query)
                return conn.name, events
            except Exception as exc:  # noqa: BLE001 — isolate per-connector failures
                logger.warning("connector_search_failed", connector=conn.name, error=str(exc))
                return conn.name, []

        pairs = await asyncio.gather(*[_one(c) for c in connectors])
        return {name: events for name, events in pairs}

    async def parallel_aggregate(
        self, query: SearchQuery, field: str, *, size: int = 10
    ) -> list[AggregateResult]:
        connectors = self._select(query.platforms)

        async def _one(conn: LogConnector) -> AggregateResult | None:
            try:
                return await conn.aggregate(query, field, size=size)
            except Exception as exc:  # noqa: BLE001
                logger.warning("connector_aggregate_failed", connector=conn.name, error=str(exc))
                return None

        results = await asyncio.gather(*[_one(c) for c in connectors])
        return [r for r in results if r is not None]

    async def parallel_timeline(self, query: SearchQuery) -> list[TimelineEvent]:
        connectors = self._select(query.platforms)

        async def _one(conn: LogConnector) -> list[TimelineEvent]:
            try:
                return await conn.timeline(query)
            except Exception as exc:  # noqa: BLE001
                logger.warning("connector_timeline_failed", connector=conn.name, error=str(exc))
                return []

        nested = await asyncio.gather(*[_one(c) for c in connectors])
        events = [e for batch in nested for e in batch]
        events.sort(key=lambda e: e.timestamp)
        return events

    async def health_all(self) -> list[dict[str, Any]]:
        return list(await asyncio.gather(*[c.health() for c in self._connectors.values()]))

    def _select(self, platforms: list[str] | None) -> list[LogConnector]:
        if not platforms:
            return self.list()
        wanted = {p.lower() for p in platforms}
        return [c for c in self._connectors.values() if c.platform.lower() in wanted]


_registry: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
        _bootstrap_mock_connectors(_registry)
    return _registry


def get_all_connectors() -> list[LogConnector]:
    return get_registry().list()


async def parallel_search(query: SearchQuery) -> dict[str, list[LogEvent]]:
    return await get_registry().parallel_search(query)


def reset_registry() -> ConnectorRegistry:
    """Rebuild registry (useful in tests)."""
    global _registry
    _registry = ConnectorRegistry()
    _bootstrap_mock_connectors(_registry)
    return _registry


def _bootstrap_mock_connectors(registry: ConnectorRegistry) -> None:
    settings = get_settings()
    # Mock mode (default) registers one connector per platform. Live mode
    # still bootstraps mocks so offline demos and CI keep working until real
    # connectors are configured via the API.
    for platform, factory in PLATFORM_FACTORIES.items():
        registry.register(factory())  # type: ignore[call-arg]
    logger.info(
        "connectors_bootstrapped",
        mode=settings.connector_mode,
        count=len(registry.list()),
    )

"""Elasticsearch connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class ElasticsearchConnector(MockPlatformConnector):
    def __init__(self, name: str = "elasticsearch-primary") -> None:
        super().__init__(platform="elasticsearch", name=name)

"""OpenSearch connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class OpenSearchConnector(MockPlatformConnector):
    def __init__(self, name: str = "opensearch-primary") -> None:
        super().__init__(platform="opensearch", name=name)

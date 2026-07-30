"""Loki connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class LokiConnector(MockPlatformConnector):
    def __init__(self, name: str = "loki-primary") -> None:
        super().__init__(platform="loki", name=name)

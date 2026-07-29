"""Graylog connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class GraylogConnector(MockPlatformConnector):
    def __init__(self, name: str = "graylog-primary") -> None:
        super().__init__(platform="graylog", name=name)

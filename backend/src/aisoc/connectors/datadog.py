"""Datadog connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class DatadogConnector(MockPlatformConnector):
    def __init__(self, name: str = "datadog-primary") -> None:
        super().__init__(platform="datadog", name=name)

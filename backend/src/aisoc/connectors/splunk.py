"""Splunk connector (mock-backed)."""

from __future__ import annotations

from aisoc.connectors.mocks.connector import MockPlatformConnector


class SplunkConnector(MockPlatformConnector):
    def __init__(self, name: str = "splunk-primary") -> None:
        super().__init__(platform="splunk", name=name)

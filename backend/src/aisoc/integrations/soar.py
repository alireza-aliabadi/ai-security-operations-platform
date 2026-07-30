"""Notification / ticketing stubs for future SOAR integrations."""

from __future__ import annotations

from typing import Any, Protocol

from aisoc.core.logging import get_logger

logger = get_logger(__name__)


class Notifier(Protocol):
    async def send(self, title: str, body: str, **kwargs: Any) -> dict[str, Any]: ...


class StubNotifier:
    """No-op notifier that logs outbound messages (Slack/Teams/Jira/ServiceNow)."""

    def __init__(self, channel: str) -> None:
        self.channel = channel

    async def send(self, title: str, body: str, **kwargs: Any) -> dict[str, Any]:
        logger.info("soar_stub_send", channel=self.channel, title=title, extra=kwargs)
        return {"ok": True, "channel": self.channel, "stub": True, "title": title}


def get_notifiers() -> dict[str, StubNotifier]:
    return {
        "slack": StubNotifier("slack"),
        "teams": StubNotifier("teams"),
        "jira": StubNotifier("jira"),
        "servicenow": StubNotifier("servicenow"),
    }

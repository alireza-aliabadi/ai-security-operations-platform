"""Shared mock connector that filters the deterministic corpus by platform."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from aisoc.connectors.base import (
    AggregateResult,
    BaseLogConnector,
    LogEvent,
    SearchQuery,
    TimelineEvent,
)
from aisoc.connectors.mocks.data import all_indices_for_platform, events_for_platform


def _matches(event: dict[str, Any], query: SearchQuery) -> bool:
    q = (query.query or "").strip().lower()
    haystack = " ".join(
        [
            str(event.get("message", "")),
            str(event.get("host", "")),
            str(event.get("user", "")),
            str(event.get("src_ip", "")),
            str(event.get("dst_ip", "")),
            str(event.get("process", "")),
            " ".join(event.get("tags") or []),
            " ".join(str(v) for v in (event.get("raw") or {}).values()),
        ]
    ).lower()
    if q and q not in {"*", "all"}:
        # Match full phrase OR any whitespace-separated token (keyword search)
        tokens = [t for t in q.split() if t]
        if tokens:
            if not any(token in haystack for token in tokens):
                return False
        elif q not in haystack:
            return False

    if query.indices and event.get("index") not in query.indices:
        return False

    ts: datetime = event["timestamp"]
    if query.start and ts < query.start:
        return False
    if query.end and ts > query.end:
        return False

    for key, value in (query.filters or {}).items():
        if value is None:
            continue
        actual = event.get(key)
        if actual is None:
            actual = (event.get("raw") or {}).get(key)
        if str(actual).lower() != str(value).lower():
            return False
    return True


def _to_log_event(event: dict[str, Any]) -> LogEvent:
    raw = dict(event.get("raw") or {})
    return LogEvent(
        id=event["id"],
        timestamp=event["timestamp"],
        platform=event["platform"],
        index=event["index"],
        source=event["source"],
        message=event["message"],
        severity=event.get("severity", "info"),
        host=event.get("host"),
        user=event.get("user"),
        src_ip=event.get("src_ip"),
        dst_ip=event.get("dst_ip"),
        process=event.get("process"),
        raw=raw,
        tags=list(event.get("tags") or []),
    )


class MockPlatformConnector(BaseLogConnector):
    """Filters mock corpus events for a single platform."""

    def __init__(self, platform: str, name: str | None = None) -> None:
        self.platform = platform
        self.name = name or f"mock-{platform}"

    def _filtered(self, query: SearchQuery) -> list[dict[str, Any]]:
        events = [e for e in events_for_platform(self.platform) if _matches(e, query)]
        events.sort(key=lambda e: e["timestamp"])
        return events

    async def search(self, query: SearchQuery) -> list[LogEvent]:
        events = self._filtered(query)
        sliced = events[query.offset : query.offset + query.limit]
        return [_to_log_event(e) for e in sliced]

    async def aggregate(
        self, query: SearchQuery, field: str, *, size: int = 10
    ) -> AggregateResult:
        events = self._filtered(query)
        counter: Counter[str] = Counter()
        for event in events:
            value = event.get(field)
            if value is None:
                value = (event.get("raw") or {}).get(field)
            if value is None and field == "severity":
                value = event.get("severity")
            if value is None and field == "host":
                value = event.get("host")
            if value is None and field == "tags":
                for tag in event.get("tags") or []:
                    counter[str(tag)] += 1
                continue
            if value is not None:
                counter[str(value)] += 1
        buckets = [
            {"key": key, "count": count}
            for key, count in counter.most_common(size)
        ]
        return AggregateResult(
            field=field,
            buckets=buckets,
            total=len(events),
            platform=self.platform,
            query=query.query,
        )

    async def timeline(self, query: SearchQuery) -> list[TimelineEvent]:
        events = self._filtered(query)
        result: list[TimelineEvent] = []
        for event in events:
            title = (event.get("tags") or ["event"])[0].replace("_", " ").title()
            result.append(
                TimelineEvent(
                    timestamp=event["timestamp"],
                    title=title,
                    description=event["message"],
                    severity=event.get("severity", "info"),
                    platform=self.platform,
                    event_id=event["id"],
                    metadata={
                        "host": event.get("host"),
                        "user": event.get("user"),
                        "src_ip": event.get("src_ip"),
                        "dst_ip": event.get("dst_ip"),
                        "tags": event.get("tags"),
                    },
                )
            )
        return result

    async def health(self) -> dict[str, Any]:
        count = len(events_for_platform(self.platform))
        return {
            "status": "ok",
            "platform": self.platform,
            "name": self.name,
            "mode": "mock",
            "event_count": count,
            "indices": all_indices_for_platform(self.platform),
        }

    async def list_indices(self) -> list[str]:
        return all_indices_for_platform(self.platform)

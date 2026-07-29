"""Log connector abstractions and shared data types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class LogEvent:
    """Normalized security log event across platforms."""

    id: str
    timestamp: datetime
    platform: str
    index: str
    source: str
    message: str
    severity: str = "info"
    host: str | None = None
    user: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    process: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform,
            "index": self.index,
            "source": self.source,
            "message": self.message,
            "severity": self.severity,
            "host": self.host,
            "user": self.user,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "process": self.process,
            "raw": self.raw,
            "tags": self.tags,
        }


@dataclass(slots=True)
class SearchQuery:
    """Cross-platform log search request."""

    query: str
    platforms: list[str] | None = None
    indices: list[str] | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int = 100
    offset: int = 0
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AggregateResult:
    """Aggregation bucket result."""

    field: str
    buckets: list[dict[str, Any]]
    total: int
    platform: str
    query: str


@dataclass(slots=True)
class TimelineEvent:
    """Chronological event for investigation timelines."""

    timestamp: datetime
    title: str
    description: str
    severity: str
    platform: str
    event_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "platform": self.platform,
            "event_id": self.event_id,
            "metadata": self.metadata,
        }


@runtime_checkable
class LogConnector(Protocol):
    """Protocol for log platform connectors."""

    name: str
    platform: str

    async def search(self, query: SearchQuery) -> list[LogEvent]: ...

    async def aggregate(
        self, query: SearchQuery, field: str, *, size: int = 10
    ) -> AggregateResult: ...

    async def timeline(self, query: SearchQuery) -> list[TimelineEvent]: ...

    async def health(self) -> dict[str, Any]: ...

    async def list_indices(self) -> list[str]: ...


class BaseLogConnector(ABC):
    """Abstract base for concrete connectors."""

    name: str
    platform: str

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[LogEvent]:
        raise NotImplementedError

    @abstractmethod
    async def aggregate(
        self, query: SearchQuery, field: str, *, size: int = 10
    ) -> AggregateResult:
        raise NotImplementedError

    @abstractmethod
    async def timeline(self, query: SearchQuery) -> list[TimelineEvent]:
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def list_indices(self) -> list[str]:
        raise NotImplementedError

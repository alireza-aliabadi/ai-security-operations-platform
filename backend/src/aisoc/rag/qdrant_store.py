"""Qdrant vector store with in-memory fallback."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger
from aisoc.rag.embeddings import EMBEDDING_DIM

logger = get_logger(__name__)


@dataclass
class StoredPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any]


@dataclass
class SearchHit:
    id: str
    score: float
    payload: dict[str, Any]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


@dataclass
class InMemoryCollection:
    name: str
    vector_size: int
    points: dict[str, StoredPoint] = field(default_factory=dict)

    def upsert(self, points: list[StoredPoint]) -> None:
        for point in points:
            self.points[point.id] = point

    def search(self, vector: list[float], *, limit: int = 10) -> list[SearchHit]:
        scored = [
            SearchHit(id=p.id, score=_cosine(vector, p.vector), payload=p.payload)
            for p in self.points.values()
        ]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:limit]


class QdrantStore:
    """Thin wrapper around Qdrant; degrades to in-memory when unavailable."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.collection = self.settings.qdrant_collection
        self.vector_size = EMBEDDING_DIM
        self._client: Any | None = None
        self._memory: dict[str, InMemoryCollection] = {}
        self._use_memory = False
        self._connect()

    def _connect(self) -> None:
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url=self.settings.qdrant_url, timeout=2.0)
            # Probe connectivity
            client.get_collections()
            self._client = client
            self._use_memory = False
            logger.info("qdrant_connected", url=self.settings.qdrant_url)
        except Exception as exc:  # noqa: BLE001
            self._client = None
            self._use_memory = True
            logger.warning("qdrant_unavailable_using_memory", error=str(exc))

    def _mem(self, name: str | None = None) -> InMemoryCollection:
        coll = name or self.collection
        if coll not in self._memory:
            self._memory[coll] = InMemoryCollection(name=coll, vector_size=self.vector_size)
        return self._memory[coll]

    def ensure_collection(self, name: str | None = None, vector_size: int | None = None) -> None:
        coll = name or self.collection
        size = vector_size or self.vector_size
        if self._use_memory or self._client is None:
            self._mem(coll).vector_size = size
            return
        try:
            from qdrant_client.http import models as qm

            existing = {c.name for c in self._client.get_collections().collections}
            if coll not in existing:
                self._client.create_collection(
                    collection_name=coll,
                    vectors_config=qm.VectorParams(size=size, distance=qm.Distance.COSINE),
                )
                logger.info("qdrant_collection_created", collection=coll, size=size)
        except Exception as exc:  # noqa: BLE001
            logger.warning("qdrant_ensure_failed_fallback", error=str(exc))
            self._use_memory = True
            self._mem(coll).vector_size = size

    def upsert(
        self,
        points: list[dict[str, Any]],
        *,
        collection: str | None = None,
    ) -> list[str]:
        """Upsert points: each dict needs vector + payload; optional id."""
        coll = collection or self.collection
        self.ensure_collection(coll)
        ids: list[str] = []
        stored: list[StoredPoint] = []
        for item in points:
            pid = str(item.get("id") or uuid.uuid4())
            vector = list(item["vector"])
            payload = dict(item.get("payload") or {})
            ids.append(pid)
            stored.append(StoredPoint(id=pid, vector=vector, payload=payload))

        if self._use_memory or self._client is None:
            self._mem(coll).upsert(stored)
            return ids

        try:
            from qdrant_client.http import models as qm

            self._client.upsert(
                collection_name=coll,
                points=[
                    qm.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in stored
                ],
            )
            return ids
        except Exception as exc:  # noqa: BLE001
            logger.warning("qdrant_upsert_failed_fallback", error=str(exc))
            self._use_memory = True
            self._mem(coll).upsert(stored)
            return ids

    def search(
        self,
        vector: list[float],
        *,
        limit: int = 10,
        collection: str | None = None,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        coll = collection or self.collection
        self.ensure_collection(coll)

        if self._use_memory or self._client is None:
            hits = self._mem(coll).search(vector, limit=limit * 3 if filter_payload else limit)
            if filter_payload:
                hits = [
                    h
                    for h in hits
                    if all(h.payload.get(k) == v for k, v in filter_payload.items())
                ]
            return hits[:limit]

        try:
            from qdrant_client.http import models as qm

            qfilter = None
            if filter_payload:
                qfilter = qm.Filter(
                    must=[
                        qm.FieldCondition(key=k, match=qm.MatchValue(value=v))
                        for k, v in filter_payload.items()
                    ]
                )
            results = self._client.search(
                collection_name=coll,
                query_vector=vector,
                limit=limit,
                query_filter=qfilter,
            )
            return [
                SearchHit(
                    id=str(r.id),
                    score=float(r.score or 0.0),
                    payload=dict(r.payload or {}),
                )
                for r in results
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("qdrant_search_failed_fallback", error=str(exc))
            self._use_memory = True
            return self.search(
                vector, limit=limit, collection=coll, filter_payload=filter_payload
            )


_store: QdrantStore | None = None


def get_qdrant_store() -> QdrantStore:
    global _store
    if _store is None:
        _store = QdrantStore()
    return _store

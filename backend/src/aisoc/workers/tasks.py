"""Celery background tasks for investigations, RAG ingest, and IOC enrichment."""

from __future__ import annotations

import asyncio
from typing import Any

from aisoc.core.logging import get_logger, setup_logging
from aisoc.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


@celery_app.task(name="aisoc.run_investigation", bind=True, max_retries=2)
def run_investigation_task(self: Any, investigation_id: str, actor_id: str | None = None) -> dict[str, Any]:
    """Run the LangGraph investigation pipeline for a persisted investigation."""
    setup_logging()

    async def _inner() -> dict[str, Any]:
        from aisoc.db.session import get_session_factory
        from aisoc.services.investigation import get_investigation, run_investigation_graph

        factory = get_session_factory()
        async with factory() as session:
            inv = await get_investigation(session, investigation_id)
            if inv is None:
                return {"ok": False, "error": "investigation_not_found", "id": investigation_id}
            try:
                await run_investigation_graph(session, inv, actor_id=actor_id)
                await session.commit()
                return {
                    "ok": True,
                    "id": investigation_id,
                    "status": inv.status,
                    "severity": inv.severity,
                    "confidence": inv.confidence,
                }
            except Exception as exc:
                await session.rollback()
                logger.exception("run_investigation_task_failed", id=investigation_id)
                raise self.retry(exc=exc, countdown=5) from exc

    return _run_async(_inner())


@celery_app.task(name="aisoc.ingest_knowledge")
def ingest_knowledge_task(seed: bool = True, documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Ingest seed knowledge or arbitrary documents into the vector store."""
    setup_logging()

    async def _inner() -> dict[str, Any]:
        from aisoc.rag.ingest import ingest_documents, ingest_seed_knowledge

        if documents:
            return await ingest_documents(documents)
        if seed:
            return await ingest_seed_knowledge()
        return {"ingested": 0, "ids": []}

    return _run_async(_inner())


@celery_app.task(name="aisoc.enrich_ioc")
def enrich_ioc_task(
    iocs: dict[str, list[str]] | list[dict[str, str]] | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """Enrich IOCs via threat intel providers (with Redis cache when available)."""
    setup_logging()

    async def _inner() -> dict[str, Any]:
        from aisoc.threat_intel.service import enrich_iocs

        return await enrich_iocs(iocs, text=text)

    return _run_async(_inner())

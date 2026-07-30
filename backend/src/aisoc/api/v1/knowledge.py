"""Knowledge search and ingest API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from aisoc.api.deps import require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import User
from aisoc.rag.hybrid import hybrid_search
from aisoc.rag.ingest import ingest_documents, ingest_seed_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=50)
    doc_type: str | None = None


class KnowledgeSearchResponse(BaseModel):
    results: list[dict[str, Any]]
    total: int


class KnowledgeIngestRequest(BaseModel):
    seed: bool = True
    documents: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeIngestResponse(BaseModel):
    ingested: int
    ids: list[str]
    doc_types: list[str] = Field(default_factory=list)
    sources: list[Any] = Field(default_factory=list)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    body: KnowledgeSearchRequest,
    _: User = Depends(require_permissions(Permission.KNOWLEDGE_READ)),
) -> KnowledgeSearchResponse:
    results = await hybrid_search(body.query, limit=body.limit, doc_type=body.doc_type)
    return KnowledgeSearchResponse(results=results, total=len(results))


@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest_knowledge(
    body: KnowledgeIngestRequest,
    _: User = Depends(require_permissions(Permission.KNOWLEDGE_WRITE)),
) -> KnowledgeIngestResponse:
    if body.documents:
        result = await ingest_documents(body.documents)
        return KnowledgeIngestResponse(
            ingested=int(result.get("ingested") or 0),
            ids=list(result.get("ids") or []),
        )
    result = await ingest_seed_knowledge()
    return KnowledgeIngestResponse(
        ingested=int(result.get("ingested") or 0),
        ids=list(result.get("ids") or []),
        doc_types=list(result.get("doc_types") or []),
        sources=list(result.get("sources") or []),
    )

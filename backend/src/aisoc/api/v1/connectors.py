"""Connector configuration and search API."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from aisoc.api.deps import DbSession, require_permissions
from aisoc.connectors.base import SearchQuery
from aisoc.connectors.registry import PLATFORM_FACTORIES, get_registry
from aisoc.core.rbac import Permission
from aisoc.core.security import encrypt_secret
from aisoc.db.models import ConnectorConfig, User
from aisoc.schemas.connectors import (
    ConnectorCreate,
    ConnectorListResponse,
    ConnectorRead,
    ConnectorUpdate,
)
from aisoc.services.audit import write_audit

router = APIRouter(prefix="/connectors", tags=["connectors"])


class SearchRequest(BaseModel):
    query: str = "*"
    platforms: list[str] | None = None
    indices: list[str] | None = None
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    filters: dict[str, Any] = Field(default_factory=dict)


class AggregateRequest(SearchRequest):
    field: str = "severity"
    size: int = Field(default=10, ge=1, le=100)


def _to_read(row: ConnectorConfig) -> ConnectorRead:
    return ConnectorRead(
        id=row.id,
        name=row.name,
        platform=row.platform,  # type: ignore[arg-type]
        base_url=row.base_url,
        enabled=row.enabled,
        meta=row.meta or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        has_credentials=bool(row.encrypted_credentials),
    )


@router.get("", response_model=ConnectorListResponse)
async def list_connectors(
    db: DbSession,
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> ConnectorListResponse:
    rows = list((await db.scalars(select(ConnectorConfig).order_by(ConnectorConfig.name))).all())
    total = len(rows)
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return ConnectorListResponse(
        items=[_to_read(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
async def create_connector(
    body: ConnectorCreate,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.CONNECTORS_WRITE)),
) -> ConnectorRead:
    existing = await db.scalar(select(ConnectorConfig).where(ConnectorConfig.name == body.name))
    if existing:
        raise HTTPException(status_code=409, detail="Connector name already exists")

    encrypted = encrypt_secret(json.dumps(body.credentials)) if body.credentials else ""
    row = ConnectorConfig(
        name=body.name,
        platform=body.platform.value,
        base_url=str(body.base_url),
        encrypted_credentials=encrypted,
        enabled=body.enabled,
        meta=body.meta,
    )
    db.add(row)
    await db.flush()

    factory = PLATFORM_FACTORIES.get(body.platform.value)
    if factory is not None:
        get_registry().register(factory(name=body.name))  # type: ignore[call-arg]

    await write_audit(
        db,
        actor_id=user.id,
        action="connector.created",
        resource_type="connector",
        resource_id=row.id,
        details={"name": row.name, "platform": row.platform},
    )
    return _to_read(row)


@router.get("/runtime/health")
async def connectors_health(
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
) -> dict[str, Any]:
    health = await get_registry().health_all()
    return {"connectors": health}


@router.post("/search")
async def search_logs(
    body: SearchRequest,
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
) -> dict[str, Any]:
    query = SearchQuery(
        query=body.query,
        platforms=body.platforms,
        indices=body.indices,
        start=body.start,
        end=body.end,
        limit=body.limit,
        offset=body.offset,
        filters=body.filters,
    )
    results = await get_registry().parallel_search(query)
    return {
        "results": {name: [e.to_dict() for e in events] for name, events in results.items()},
        "total": sum(len(v) for v in results.values()),
    }


@router.post("/aggregate")
async def aggregate_logs(
    body: AggregateRequest,
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
) -> dict[str, Any]:
    query = SearchQuery(
        query=body.query,
        platforms=body.platforms,
        indices=body.indices,
        start=body.start,
        end=body.end,
        limit=body.limit,
        offset=body.offset,
        filters=body.filters,
    )
    results = await get_registry().parallel_aggregate(query, body.field, size=body.size)
    return {
        "results": [
            {
                "field": r.field,
                "buckets": r.buckets,
                "total": r.total,
                "platform": r.platform,
                "query": r.query,
            }
            for r in results
        ]
    }


@router.post("/timeline")
async def timeline_logs(
    body: SearchRequest,
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
) -> dict[str, Any]:
    query = SearchQuery(
        query=body.query,
        platforms=body.platforms,
        indices=body.indices,
        start=body.start,
        end=body.end,
        limit=body.limit,
        offset=body.offset,
        filters=body.filters,
    )
    events = await get_registry().parallel_timeline(query)
    return {"events": [e.to_dict() for e in events], "total": len(events)}


@router.get("/{connector_id}", response_model=ConnectorRead)
async def get_connector(
    connector_id: str,
    db: DbSession,
    _: User = Depends(require_permissions(Permission.CONNECTORS_READ)),
) -> ConnectorRead:
    row = await db.scalar(select(ConnectorConfig).where(ConnectorConfig.id == connector_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return _to_read(row)


@router.patch("/{connector_id}", response_model=ConnectorRead)
async def update_connector(
    connector_id: str,
    body: ConnectorUpdate,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.CONNECTORS_WRITE)),
) -> ConnectorRead:
    row = await db.scalar(select(ConnectorConfig).where(ConnectorConfig.id == connector_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    if body.name is not None:
        row.name = body.name
    if body.base_url is not None:
        row.base_url = body.base_url
    if body.enabled is not None:
        row.enabled = body.enabled
    if body.meta is not None:
        row.meta = body.meta
    if body.credentials is not None:
        row.encrypted_credentials = encrypt_secret(json.dumps(body.credentials))
    await db.flush()
    await write_audit(
        db,
        actor_id=user.id,
        action="connector.updated",
        resource_type="connector",
        resource_id=row.id,
        details={"name": row.name},
    )
    return _to_read(row)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_connector(
    connector_id: str,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.CONNECTORS_WRITE)),
) -> Response:
    row = await db.scalar(select(ConnectorConfig).where(ConnectorConfig.id == connector_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    get_registry().unregister(row.name)
    await db.delete(row)
    await write_audit(
        db,
        actor_id=user.id,
        action="connector.deleted",
        resource_type="connector",
        resource_id=connector_id,
        details={"name": row.name},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

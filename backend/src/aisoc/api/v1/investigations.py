"""Investigations CRUD and run/stream endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from aisoc.agents.streaming import format_sse
from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import Investigation, InvestigationStatus, User
from aisoc.schemas.investigations import (
    InvestigationCreate,
    InvestigationListResponse,
    InvestigationRead,
    InvestigationUpdate,
)
from aisoc.services.audit import write_audit
from aisoc.services.investigation import (
    apply_state_to_investigation,
    create_investigation,
    investigation_event_stream,
    run_investigation_graph,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=InvestigationListResponse)
async def list_investigations(
    db: DbSession,
    _: User = Depends(require_permissions(Permission.INVESTIGATIONS_READ)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> InvestigationListResponse:
    rows = list(
        (
            await db.scalars(select(Investigation).order_by(Investigation.created_at.desc()))
        ).all()
    )
    total = len(rows)
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return InvestigationListResponse(
        items=[InvestigationRead.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=InvestigationRead, status_code=status.HTTP_201_CREATED)
async def create_investigation_endpoint(
    body: InvestigationCreate,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.INVESTIGATIONS_WRITE)),
) -> InvestigationRead:
    inv = await create_investigation(
        db,
        title=body.title,
        query=body.query,
        created_by=user.id,
    )
    return InvestigationRead.model_validate(inv)


@router.get("/{investigation_id}", response_model=InvestigationRead)
async def get_investigation(
    investigation_id: str,
    db: DbSession,
    _: User = Depends(require_permissions(Permission.INVESTIGATIONS_READ)),
) -> InvestigationRead:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationRead.model_validate(inv)


@router.patch("/{investigation_id}", response_model=InvestigationRead)
async def update_investigation(
    investigation_id: str,
    body: InvestigationUpdate,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.INVESTIGATIONS_WRITE)),
) -> InvestigationRead:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(inv, key, value)
    await db.flush()
    await write_audit(
        db,
        actor_id=user.id,
        action="investigation.updated",
        resource_type="investigation",
        resource_id=inv.id,
        details={"fields": list(data.keys())},
    )
    return InvestigationRead.model_validate(inv)


@router.delete(
    "/{investigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_investigation(
    investigation_id: str,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.INVESTIGATIONS_WRITE)),
) -> Response:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    await db.delete(inv)
    await write_audit(
        db,
        actor_id=user.id,
        action="investigation.deleted",
        resource_type="investigation",
        resource_id=investigation_id,
        details={},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{investigation_id}/run", response_model=InvestigationRead)
async def run_investigation_endpoint(
    investigation_id: str,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.INVESTIGATIONS_WRITE)),
    interrupt_before_export: bool = Query(False),
) -> InvestigationRead:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if inv.status == InvestigationStatus.RUNNING.value:
        raise HTTPException(status_code=409, detail="Investigation already running")
    inv = await run_investigation_graph(
        db,
        inv,
        actor_id=user.id,
        interrupt_before_export=interrupt_before_export,
    )
    return InvestigationRead.model_validate(inv)


@router.get("/{investigation_id}/stream")
async def stream_investigation_endpoint(
    investigation_id: str,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.INVESTIGATIONS_READ)),
    interrupt_before_export: bool = Query(False),
) -> StreamingResponse:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    async def event_gen() -> AsyncIterator[str]:
        inv.status = InvestigationStatus.RUNNING.value
        await db.flush()
        final_state = None
        async for event in investigation_event_stream(
            inv.query,
            investigation_id=inv.id,
            interrupt_before_export=interrupt_before_export,
        ):
            if event.get("type") == "completed":
                final_state = (event.get("data") or {}).get("state")
            yield format_sse(event)
        if final_state is not None:
            await apply_state_to_investigation(
                db,
                inv,
                final_state,
                actor_id=user.id,
            )

    return StreamingResponse(event_gen(), media_type="text/event-stream")

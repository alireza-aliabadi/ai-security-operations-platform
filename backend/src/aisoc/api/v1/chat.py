"""SSE chat endpoint that streams the investigation graph."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from aisoc.agents.streaming import format_sse, stream_investigation
from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import ChatMessage, Investigation, InvestigationStatus, User
from aisoc.services.investigation import apply_state_to_investigation, create_investigation

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    investigation_id: str | None = None
    title: str | None = None
    interrupt_before_export: bool = False
    persist: bool = True


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.CHAT_USE)),
) -> StreamingResponse:
    investigation: Investigation | None = None
    if body.investigation_id:
        investigation = await db.get(Investigation, body.investigation_id)
    if investigation is None and body.persist:
        investigation = await create_investigation(
            db,
            title=body.title or body.message[:80],
            query=body.message,
            created_by=user.id,
        )

    db.add(
        ChatMessage(
            investigation_id=investigation.id if investigation else None,
            user_id=user.id,
            role="user",
            content=body.message,
            meta={},
        )
    )
    await db.flush()

    investigation_id = investigation.id if investigation else ""
    query = investigation.query if investigation else body.message

    async def event_gen() -> AsyncIterator[str]:
        if investigation is not None:
            investigation.status = InvestigationStatus.RUNNING.value
            await db.flush()

        final_state = None
        async for event in stream_investigation(
            query,
            investigation_id=investigation_id,
            interrupt_before_export=body.interrupt_before_export,
        ):
            if event.get("type") == "completed":
                final_state = (event.get("data") or {}).get("state")
            yield format_sse(event)

        if investigation is not None and final_state is not None:
            await apply_state_to_investigation(
                db,
                investigation,
                final_state,
                actor_id=user.id,
            )
            summary = (
                final_state.get("executive_report")
                or final_state.get("root_cause")
                or "Investigation completed."
            )
            db.add(
                ChatMessage(
                    investigation_id=investigation.id,
                    user_id=None,
                    role="assistant",
                    content=str(summary),
                    meta={
                        "severity": final_state.get("severity"),
                        "confidence": final_state.get("confidence"),
                    },
                )
            )
            await db.flush()
            yield format_sse(
                {
                    "type": "persisted",
                    "agent": "chat",
                    "content": "Investigation results saved",
                    "data": {"investigation_id": investigation.id},
                }
            )

    return StreamingResponse(event_gen(), media_type="text/event-stream")

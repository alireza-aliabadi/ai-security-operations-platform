"""Investigation lifecycle service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.agents.graph import run_investigation
from aisoc.agents.state import InvestigationState
from aisoc.agents.streaming import stream_investigation
from aisoc.db.models import Investigation, InvestigationStatus
from aisoc.services.approval import create_approval
from aisoc.services.audit import write_audit


def _state_to_fields(state: InvestigationState) -> dict[str, Any]:
    remediation = state.get("remediation") or []
    if isinstance(remediation, list):
        remediation_text = "\n".join(f"- {item}" for item in remediation)
    else:
        remediation_text = str(remediation)

    iocs = state.get("iocs") or {}
    # Model stores iocs as JSON list; keep structured dict wrapped for compatibility
    iocs_value: Any
    if isinstance(iocs, dict):
        iocs_value = [
            {"type": "ip", "value": v} for v in iocs.get("ips", [])
        ] + [
            {"type": "domain", "value": v} for v in iocs.get("domains", [])
        ] + [
            {"type": "hash", "value": v} for v in iocs.get("hashes", [])
        ]
    else:
        iocs_value = iocs

    logs = state.get("logs") or []
    timeline = [
        {
            "timestamp": log.get("timestamp"),
            "title": (log.get("tags") or ["event"])[0] if log.get("tags") else "event",
            "description": log.get("message"),
            "severity": log.get("severity"),
            "platform": log.get("platform"),
            "event_id": log.get("id"),
        }
        for log in logs
    ]

    return {
        "status": InvestigationStatus.COMPLETED.value,
        "result": {
            "analysis": state.get("analysis"),
            "correlated": state.get("correlated"),
            "rag_context": state.get("rag_context"),
            "plan": state.get("plan"),
            "errors": state.get("errors"),
        },
        "agent_trace": state.get("agent_trace") or [],
        "severity": state.get("severity"),
        "confidence": state.get("confidence"),
        "keywords": state.get("keywords") or [],
        "timeline": timeline,
        "iocs": iocs_value,
        "mitre": state.get("mitre") or [],
        "root_cause": state.get("root_cause"),
        "remediation": remediation_text,
        "executive_report": state.get("executive_report"),
        "technical_report": state.get("technical_report"),
    }


async def create_investigation(
    session: AsyncSession,
    *,
    title: str,
    query: str,
    created_by: str | None,
    ip: str | None = None,
) -> Investigation:
    investigation = Investigation(
        title=title,
        query=query,
        status=InvestigationStatus.PENDING.value,
        created_by=created_by,
    )
    session.add(investigation)
    await session.flush()
    await write_audit(
        session,
        actor_id=created_by,
        action="investigation.created",
        resource_type="investigation",
        resource_id=investigation.id,
        details={"title": title, "query": query},
        ip=ip,
    )
    return investigation


async def get_investigation(session: AsyncSession, investigation_id: str) -> Investigation | None:
    return await session.scalar(select(Investigation).where(Investigation.id == investigation_id))


async def list_investigations(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    created_by: str | None = None,
) -> tuple[list[Investigation], int]:
    stmt = select(Investigation).order_by(Investigation.created_at.desc())
    if created_by:
        stmt = stmt.where(Investigation.created_by == created_by)
    result = await session.scalars(stmt)
    items = list(result.all())
    total = len(items)
    start = (page - 1) * page_size
    return items[start : start + page_size], total


async def run_investigation_graph(
    session: AsyncSession,
    investigation: Investigation,
    *,
    actor_id: str | None = None,
    interrupt_before_export: bool = False,
    ip: str | None = None,
) -> Investigation:
    investigation.status = InvestigationStatus.RUNNING.value
    await session.flush()

    try:
        state = await run_investigation(
            investigation.query,
            investigation_id=investigation.id,
            interrupt_before_export=interrupt_before_export,
        )
        fields = _state_to_fields(state)
        for key, value in fields.items():
            setattr(investigation, key, value)

        if state.get("approvals_needed"):
            investigation.status = InvestigationStatus.AWAITING_APPROVAL.value
            for item in state["approvals_needed"]:
                await create_approval(
                    session,
                    investigation_id=investigation.id,
                    action=str(item.get("action") or "export_report"),
                    requested_by=actor_id,
                    reason=str(item.get("reason") or ""),
                    ip=ip,
                )
        await session.flush()
        await write_audit(
            session,
            actor_id=actor_id,
            action="investigation.completed",
            resource_type="investigation",
            resource_id=investigation.id,
            details={
                "severity": investigation.severity,
                "confidence": investigation.confidence,
                "status": investigation.status,
            },
            ip=ip,
        )
    except Exception as exc:
        investigation.status = InvestigationStatus.FAILED.value
        investigation.result = {"error": str(exc)}
        await session.flush()
        await write_audit(
            session,
            actor_id=actor_id,
            action="investigation.failed",
            resource_type="investigation",
            resource_id=investigation.id,
            details={"error": str(exc)},
            ip=ip,
        )
        raise

    return investigation


async def apply_state_to_investigation(
    session: AsyncSession,
    investigation: Investigation,
    state: InvestigationState,
    *,
    actor_id: str | None = None,
    ip: str | None = None,
) -> Investigation:
    fields = _state_to_fields(state)
    for key, value in fields.items():
        setattr(investigation, key, value)
    if state.get("approvals_needed"):
        investigation.status = InvestigationStatus.AWAITING_APPROVAL.value
    await session.flush()
    await write_audit(
        session,
        actor_id=actor_id,
        action="investigation.updated_from_stream",
        resource_type="investigation",
        resource_id=investigation.id,
        details={"status": investigation.status},
        ip=ip,
    )
    return investigation


def investigation_event_stream(
    query: str,
    *,
    investigation_id: str = "",
    interrupt_before_export: bool = False,
):
    return stream_investigation(
        query,
        investigation_id=investigation_id,
        interrupt_before_export=interrupt_before_export,
    )

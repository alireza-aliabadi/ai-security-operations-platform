"""Investigation report retrieval and export."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select

from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import Investigation, User
from aisoc.services.audit import write_audit

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{investigation_id}")
async def get_reports(
    investigation_id: str,
    db: DbSession,
    _: User = Depends(require_permissions(Permission.REPORTS_READ)),
) -> dict[str, Any]:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "investigation_id": inv.id,
        "title": inv.title,
        "severity": inv.severity,
        "confidence": inv.confidence,
        "executive_report": inv.executive_report,
        "technical_report": inv.technical_report,
        "root_cause": inv.root_cause,
        "remediation": inv.remediation,
        "mitre": inv.mitre,
        "iocs": inv.iocs,
        "timeline": inv.timeline,
        "keywords": inv.keywords,
        "status": inv.status,
    }


@router.get("/{investigation_id}/export")
async def export_report(
    investigation_id: str,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.REPORTS_EXPORT)),
    format: str = Query("markdown", pattern="^(markdown|json|text)$"),
) -> Response:
    inv = await db.scalar(select(Investigation).where(Investigation.id == investigation_id))
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    await write_audit(
        db,
        actor_id=user.id,
        action="report.exported",
        resource_type="investigation",
        resource_id=inv.id,
        details={"format": format},
    )

    if format == "json":
        import json

        payload = {
            "investigation_id": inv.id,
            "title": inv.title,
            "executive_report": inv.executive_report,
            "technical_report": inv.technical_report,
            "severity": inv.severity,
            "confidence": inv.confidence,
            "root_cause": inv.root_cause,
            "remediation": inv.remediation,
            "mitre": inv.mitre,
            "iocs": inv.iocs,
        }
        return Response(
            content=json.dumps(payload, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="investigation-{inv.id}.json"'
            },
        )

    md = "\n".join(
        [
            f"# {inv.title}",
            "",
            f"**Severity:** {inv.severity or 'n/a'}  ",
            f"**Confidence:** {inv.confidence if inv.confidence is not None else 'n/a'}",
            "",
            "## Executive Summary",
            inv.executive_report or "_No executive report_",
            "",
            "## Root Cause",
            inv.root_cause or "_n/a_",
            "",
            "## Remediation",
            inv.remediation or "_n/a_",
            "",
            "## Technical Report",
            inv.technical_report or "_No technical report_",
            "",
        ]
    )
    media = "text/markdown" if format == "markdown" else "text/plain"
    ext = "md" if format == "markdown" else "txt"
    return PlainTextResponse(
        content=md,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="investigation-{inv.id}.{ext}"'},
    )

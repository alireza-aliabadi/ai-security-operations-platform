"""Threat intel enrichment API (used by MCP lookup_ioc and analysts)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from aisoc.api.deps import require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import User
from aisoc.threat_intel.extractors import extract_iocs
from aisoc.threat_intel.service import enrich_iocs

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])


class EnrichRequest(BaseModel):
    text: str | None = None
    iocs: dict[str, list[str]] | None = None
    value: str | None = Field(default=None, description="Single IOC value")
    type: str | None = Field(default=None, description="Single IOC type: ip|domain|hash|cve")


@router.post("/enrich")
async def enrich_endpoint(
    body: EnrichRequest,
    _: User = Depends(require_permissions(Permission.INVESTIGATIONS_READ)),
) -> dict[str, Any]:
    if body.value and body.type:
        return await enrich_iocs([{"type": body.type, "value": body.value}])
    if body.iocs:
        return await enrich_iocs(body.iocs)
    if body.text:
        return await enrich_iocs(text=body.text)
    return {"items": [], "by_type": {}, "summary": {"total": 0, "malicious": 0, "max_score": 0}}


@router.post("/extract")
async def extract_endpoint(
    body: EnrichRequest,
    _: User = Depends(require_permissions(Permission.INVESTIGATIONS_READ)),
) -> dict[str, list[str]]:
    return extract_iocs(body.text or "")

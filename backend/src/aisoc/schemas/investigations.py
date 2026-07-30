"""Investigation and approval schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aisoc.db.models import ApprovalStatus, InvestigationStatus
from aisoc.schemas.common import ORMModel


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    query: str = Field(min_length=1)


class InvestigationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    query: str | None = Field(default=None, min_length=1)
    status: InvestigationStatus | None = None
    severity: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    keywords: list[Any] | None = None
    timeline: list[Any] | None = None
    iocs: list[Any] | None = None
    mitre: list[Any] | None = None
    root_cause: str | None = None
    remediation: str | None = None
    executive_report: str | None = None
    technical_report: str | None = None
    result: dict[str, Any] | None = None
    agent_trace: list[Any] | None = None


class InvestigationRead(ORMModel):
    id: str
    title: str
    query: str
    status: InvestigationStatus
    created_by: str | None
    result: dict[str, Any] | None = None
    agent_trace: list[Any] | None = None
    severity: str | None = None
    confidence: float | None = None
    keywords: list[Any] | None = None
    timeline: list[Any] | None = None
    iocs: list[Any] | None = None
    mitre: list[Any] | None = None
    root_cause: str | None = None
    remediation: str | None = None
    executive_report: str | None = None
    technical_report: str | None = None
    created_at: datetime
    updated_at: datetime


class InvestigationListResponse(BaseModel):
    items: list[InvestigationRead]
    total: int
    page: int
    page_size: int


class ApprovalCreate(BaseModel):
    investigation_id: str
    action: str = Field(min_length=1, max_length=255)
    reason: str | None = None


class ApprovalDecide(BaseModel):
    status: ApprovalStatus
    reason: str | None = None


class ApprovalRead(ORMModel):
    id: str
    investigation_id: str
    action: str
    status: ApprovalStatus
    requested_by: str | None
    decided_by: str | None
    reason: str | None
    created_at: datetime
    decided_at: datetime | None = None


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    investigation_id: str | None = None
    role: str = "user"
    meta: dict[str, Any] = Field(default_factory=dict)


class ChatMessageRead(ORMModel):
    id: str
    investigation_id: str | None
    user_id: str | None
    role: str
    content: str
    meta: dict[str, Any]
    created_at: datetime


class SavedInvestigationCreate(BaseModel):
    investigation_id: str
    notes: str | None = None


class SavedInvestigationRead(ORMModel):
    id: str
    user_id: str
    investigation_id: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

"""Connector schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from aisoc.db.models import PlatformType
from aisoc.schemas.common import ORMModel


class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    platform: PlatformType
    base_url: str = Field(min_length=1, max_length=1024)
    credentials: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)


class ConnectorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = Field(default=None, min_length=1, max_length=1024)
    credentials: dict[str, Any] | None = None
    enabled: bool | None = None
    meta: dict[str, Any] | None = None


class ConnectorRead(ORMModel):
    id: str
    name: str
    platform: PlatformType
    base_url: str
    enabled: bool
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    has_credentials: bool = True


class ConnectorListResponse(BaseModel):
    items: list[ConnectorRead]
    total: int
    page: int
    page_size: int


class ConnectorTestRequest(BaseModel):
    base_url: HttpUrl | None = None

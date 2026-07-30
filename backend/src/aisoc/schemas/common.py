"""Shared Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

T = TypeVar("T")


def _normalize_email(value: str) -> str:
    """Validate email while allowing reserved/special-use domains (.local) for demos."""
    cleaned = value.strip().lower()
    try:
        result = validate_email(
            cleaned,
            check_deliverability=False,
            test_environment=True,
        )
        return str(result.normalized).lower()
    except TypeError:
        try:
            result = validate_email(cleaned, check_deliverability=False)
            return str(result.normalized).lower()
        except EmailNotValidError:
            pass
    except EmailNotValidError:
        pass

    if "@" not in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise ValueError("Invalid email address")
    domain = cleaned.rsplit("@", 1)[-1]
    # Demo / reserved domains used by AISOC seed users
    if domain.endswith(".local") or domain in {"localhost", "example", "test", "invalid"}:
        return cleaned
    raise ValueError("Invalid email address")


EmailAddress = Annotated[str, AfterValidator(_normalize_email)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class TimestampSchema(ORMModel):
    created_at: datetime
    updated_at: datetime | None = None


class IdSchema(ORMModel):
    id: str


class AuditLogRead(ORMModel):
    id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    ip: str | None
    created_at: datetime

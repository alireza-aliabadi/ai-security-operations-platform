"""ORM models for the AI Security Operations Platform."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aisoc.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlatformType(StrEnum):
    GRAYLOG = "graylog"
    ELASTICSEARCH = "elasticsearch"
    LOKI = "loki"
    SPLUNK = "splunk"
    OPENSEARCH = "opensearch"
    DATADOG = "datadog"


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    roles: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    oidc_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    investigations: Mapped[list[Investigation]] = relationship(
        back_populates="creator", foreign_keys="Investigation.created_by"
    )
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="user")


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class ConnectorConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "connector_configs"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class Investigation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "investigations"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(64), nullable=False, default=InvestigationStatus.PENDING, index=True
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    agent_trace: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    keywords: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    timeline: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    iocs: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    mitre: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    executive_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    creator: Mapped[User | None] = relationship(
        back_populates="investigations", foreign_keys=[created_by]
    )
    approvals: Mapped[list[Approval]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    saved_links: Mapped[list[SavedInvestigation]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )


class Approval(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "approvals"

    investigation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(64), nullable=False, default=ApprovalStatus.PENDING, index=True
    )
    requested_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    investigation: Mapped[Investigation] = relationship(back_populates="approvals")


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail — never update or delete rows in application code."""

    __tablename__ = "audit_logs"

    actor_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class KnowledgeDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)


class SavedInvestigation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "saved_investigations"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    investigation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    investigation: Mapped[Investigation] = relationship(back_populates="saved_links")


class ChatMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "chat_messages"

    investigation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    investigation: Mapped[Investigation | None] = relationship(back_populates="chat_messages")
    user: Mapped[User | None] = relationship(back_populates="chat_messages")


def new_uuid() -> str:
    return str(uuid4())

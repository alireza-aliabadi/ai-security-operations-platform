"""Database seed helpers for development and first boot."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger
from aisoc.core.rbac import Role
from aisoc.core.security import encrypt_secret, hash_password
from aisoc.db.models import ConnectorConfig, KnowledgeDocument, PlatformType, User

logger = get_logger(__name__)


async def seed_users(session: AsyncSession, settings: Settings | None = None) -> None:
    settings = settings or get_settings()

    seeds = [
        (
            settings.seed_admin_email,
            settings.seed_admin_password,
            "AISOC Admin",
            [Role.ADMIN.value],
        ),
        (
            settings.seed_analyst_email,
            settings.seed_analyst_password,
            "AISOC Analyst",
            [Role.ANALYST.value],
        ),
    ]

    for email, password, full_name, roles in seeds:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing is not None:
            continue
        session.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                is_active=True,
                roles=roles,
            )
        )
        logger.info("seed_user_created", email=email, roles=roles)


async def seed_connectors(session: AsyncSession, settings: Settings | None = None) -> None:
    settings = settings or get_settings()

    defaults: list[dict[str, object]] = [
        {
            "name": "Mock Graylog",
            "platform": PlatformType.GRAYLOG.value,
            "base_url": "http://localhost:9000",
            "credentials": {"token": "mock-graylog-token"},
            "meta": {"mode": "mock", "streams": ["security"]},
        },
        {
            "name": "Mock Elasticsearch",
            "platform": PlatformType.ELASTICSEARCH.value,
            "base_url": "http://localhost:9200",
            "credentials": {"username": "elastic", "password": "changeme"},
            "meta": {"mode": "mock", "index_pattern": "logs-*"},
        },
        {
            "name": "Mock Loki",
            "platform": PlatformType.LOKI.value,
            "base_url": "http://localhost:3100",
            "credentials": {"token": "mock-loki-token"},
            "meta": {"mode": "mock"},
        },
        {
            "name": "Mock Splunk",
            "platform": PlatformType.SPLUNK.value,
            "base_url": "https://localhost:8089",
            "credentials": {"token": "mock-splunk-token"},
            "meta": {"mode": "mock", "index": "main"},
        },
        {
            "name": "Mock OpenSearch",
            "platform": PlatformType.OPENSEARCH.value,
            "base_url": "https://localhost:9200",
            "credentials": {"username": "admin", "password": "admin"},
            "meta": {"mode": "mock"},
        },
        {
            "name": "Mock Datadog",
            "platform": PlatformType.DATADOG.value,
            "base_url": "https://api.datadoghq.com",
            "credentials": {"api_key": "mock-dd-api", "app_key": "mock-dd-app"},
            "meta": {"mode": "mock", "site": "datadoghq.com"},
        },
    ]

    for item in defaults:
        name = str(item["name"])
        existing = await session.scalar(select(ConnectorConfig).where(ConnectorConfig.name == name))
        if existing is not None:
            continue
        creds = json.dumps(item["credentials"])
        session.add(
            ConnectorConfig(
                name=name,
                platform=str(item["platform"]),
                base_url=str(item["base_url"]),
                encrypted_credentials=encrypt_secret(creds, settings),
                enabled=True,
                meta=item["meta"],  # type: ignore[arg-type]
            )
        )
        logger.info("seed_connector_created", name=name, platform=item["platform"])


async def seed_knowledge(session: AsyncSession) -> None:
    docs = [
        {
            "title": "Brute Force Detection Runbook",
            "doc_type": "runbook",
            "content": (
                "1. Confirm failed authentication spikes across identity providers.\n"
                "2. Extract source IPs and correlate with threat intel.\n"
                "3. Check for successful logins from the same sources.\n"
                "4. Contain: block malicious IPs, force password resets.\n"
                "5. Document IOCs and update detection rules."
            ),
            "metadata": {"severity": "T1110", "severity": "high"},
        },
        {
            "title": "Lateral Movement SOP",
            "doc_type": "sop",
            "content": (
                "Investigate unusual remote authentication, RDP/SSH spikes, and "
                "service account misuse. Map paths with process and network telemetry. "
                "Isolate affected hosts and rotate credentials for compromised accounts."
            ),
            "metadata": {"tactics": ["TA0008"], "severity": "critical"},
        },
        {
            "title": "Security Incident Classification Policy",
            "doc_type": "policy",
            "content": (
                "Severity levels: critical (active breach / data exfil), high (confirmed "
                "malicious activity), medium (suspicious with partial evidence), "
                "low (anomalous but likely benign). All critical and high incidents "
                "require human approval before automated remediation."
            ),
            "metadata": {"owner": "security-operations"},
        },
        {
            "title": "CVE Triage Guidance",
            "doc_type": "cve",
            "content": (
                "Prioritize CVEs with public exploits and internet-facing assets. "
                "Cross-check package inventories, patch windows, and compensating controls. "
                "Escalate zero-days affecting identity or remote access services immediately."
            ),
            "metadata": {"source": "internal-knowledge"},
        },
    ]

    for item in docs:
        title = item["title"]
        existing = await session.scalar(
            select(KnowledgeDocument).where(KnowledgeDocument.title == title)
        )
        if existing is not None:
            continue
        session.add(
            KnowledgeDocument(
                title=title,
                doc_type=item["doc_type"],
                content=item["content"],
                metadata_=item["metadata"],
                embedding_id=None,
            )
        )
        logger.info("seed_knowledge_created", title=title)


async def run_seed(session: AsyncSession, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    await seed_users(session, settings)
    await seed_connectors(session, settings)
    await seed_knowledge(session)
    await session.commit()
    logger.info("seed_complete")

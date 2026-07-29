"""Knowledge ingestion from filesystem seed docs or embedded fallbacks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aisoc.core.logging import get_logger
from aisoc.rag.embeddings import get_embedding_provider
from aisoc.rag.qdrant_store import get_qdrant_store

logger = get_logger(__name__)

DOC_TYPES = ("runbooks", "sops", "cves", "policies", "incidents")

DOC_TYPE_LABEL = {
    "runbooks": "runbook",
    "sops": "sop",
    "cves": "cve",
    "policies": "policy",
    "incidents": "incident",
}

EMBEDDED_SEED_DOCS: list[dict[str, Any]] = [
    {
        "title": "Brute Force Response Runbook",
        "doc_type": "runbook",
        "source_path": "embedded://runbooks/brute-force.md",
        "content": (
            "# Brute Force Response Runbook\n\n"
            "1. Confirm failed authentication spikes across identity providers.\n"
            "2. Extract source IPs and correlate with threat intel.\n"
            "3. Check for successful logins from the same sources.\n"
            "4. Contain: block malicious IPs, force password resets.\n"
            "5. Document IOCs and update detection rules.\n"
        ),
        "metadata": {"mitre": "T1110", "severity": "high"},
    },
    {
        "title": "C2 Containment SOP",
        "doc_type": "sop",
        "source_path": "embedded://sops/c2-containment.md",
        "content": (
            "# C2 Containment SOP\n\n"
            "Block destination IPs/domains at the perimeter, capture memory, "
            "and check for scheduled tasks/services persistence. Hunt for "
            "beaconing to 185.220.101.45 and evil.example.com patterns.\n"
        ),
        "metadata": {"severity": "critical"},
    },
    {
        "title": "CVE Triage Guidance",
        "doc_type": "cve",
        "source_path": "embedded://cves/triage.md",
        "content": (
            "# CVE Triage Guidance\n\n"
            "Prioritize CVEs with public exploits and internet-facing assets. "
            "Cross-check package inventories, patch windows, and compensating controls. "
            "Escalate zero-days affecting identity or remote access services immediately.\n"
        ),
        "metadata": {"source": "internal-knowledge"},
    },
    {
        "title": "Security Incident Classification Policy",
        "doc_type": "policy",
        "source_path": "embedded://policies/classification.md",
        "content": (
            "# Security Incident Classification Policy\n\n"
            "Severity levels: critical (active breach / data exfil), high (confirmed "
            "malicious activity), medium (suspicious with partial evidence), "
            "low (anomalous but likely benign). Critical and high incidents require "
            "human approval before automated remediation.\n"
        ),
        "metadata": {"owner": "security-operations"},
    },
    {
        "title": "Sample Credential Stuffing Incident",
        "doc_type": "incident",
        "source_path": "embedded://incidents/credential-stuffing.md",
        "content": (
            "# Incident: Credential Stuffing → C2\n\n"
            "External brute-force against jdoe succeeded, followed by malware "
            "execution and C2 to 185.220.101.45 / evil.example.com, then lateral "
            "movement to SRV-APP-12 via RDP.\n"
        ),
        "metadata": {"severity": "critical", "year": 2026},
    },
]


def resolve_knowledge_root() -> Path | None:
    """Locate workspace knowledge/ directory relative to this module."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[4] / "knowledge",
        here.parents[3] / "knowledge",
        Path.cwd() / "knowledge",
        Path.cwd().parent / "knowledge",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return None


def _title_from_markdown(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_seed_documents(knowledge_root: Path | None = None) -> list[dict[str, Any]]:
    root = knowledge_root if knowledge_root is not None else resolve_knowledge_root()
    docs: list[dict[str, Any]] = []
    if root is not None:
        for folder in DOC_TYPES:
            label = DOC_TYPE_LABEL[folder]
            directory = root / folder
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("**/*")):
                if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                    continue
                content = path.read_text(encoding="utf-8")
                docs.append(
                    {
                        "title": _title_from_markdown(content, path.stem.replace("-", " ").title()),
                        "doc_type": label,
                        "content": content,
                        "source_path": str(path.relative_to(root)),
                        "metadata": {"folder": folder},
                    }
                )
    if not docs:
        logger.warning("knowledge_seed_using_embedded")
        docs = [dict(d) for d in EMBEDDED_SEED_DOCS]
    return docs


async def ingest_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Embed and upsert documents into the vector store."""
    if not documents:
        return {"ingested": 0, "ids": []}

    store = get_qdrant_store()
    embedder = get_embedding_provider()
    store.ensure_collection()

    texts = [
        f"{d.get('title', '')}\n{d.get('doc_type', '')}\n{d.get('content', '')}" for d in documents
    ]
    vectors = await embedder.embed(texts)
    points: list[dict[str, Any]] = []
    for doc, vector in zip(documents, vectors, strict=True):
        points.append(
            {
                "vector": vector,
                "payload": {
                    "title": doc.get("title"),
                    "doc_type": doc.get("doc_type"),
                    "content": doc.get("content"),
                    "source_path": doc.get("source_path"),
                    "metadata": doc.get("metadata") or {},
                },
            }
        )
    ids = store.upsert(points)
    logger.info("knowledge_ingested", count=len(ids))
    return {"ingested": len(ids), "ids": ids}


async def ingest_seed_knowledge(knowledge_root: Path | None = None) -> dict[str, Any]:
    """Load seed markdown from knowledge/ (or embedded fallbacks) and upsert."""
    docs = load_seed_documents(knowledge_root)
    result = await ingest_documents(docs)
    result["doc_types"] = sorted({str(d.get("doc_type")) for d in docs})
    result["sources"] = [d.get("source_path") for d in docs]
    return result

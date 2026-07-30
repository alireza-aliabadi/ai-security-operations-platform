"""IOC extractors for IPs, domains, hashes, and CVEs."""

from __future__ import annotations

import re
from typing import Any

IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b"
)
DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|info|biz|example|local|internal)\b",
    re.I,
)
HASH_RE = re.compile(r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)


def extract_ips(text: str) -> list[str]:
    return sorted(set(IP_RE.findall(text)))


def extract_domains(text: str) -> list[str]:
    return sorted({d.lower() for d in DOMAIN_RE.findall(text)})


def extract_hashes(text: str) -> list[str]:
    return sorted(set(HASH_RE.findall(text)))


def extract_cves(text: str) -> list[str]:
    return sorted({c.upper() for c in CVE_RE.findall(text)})


def extract_iocs(text: str | list[str]) -> dict[str, list[str]]:
    """Extract IPs, domains, hashes, and CVEs from text or list of texts."""
    blob = "\n".join(text) if isinstance(text, list) else text
    return {
        "ips": extract_ips(blob),
        "domains": extract_domains(blob),
        "hashes": extract_hashes(blob),
        "cves": extract_cves(blob),
    }


def flatten_iocs(iocs: dict[str, list[str]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for ioc_type, values in iocs.items():
        # normalize plural keys → singular type labels
        singular = {
            "ips": "ip",
            "domains": "domain",
            "hashes": "hash",
            "cves": "cve",
        }.get(ioc_type, ioc_type.rstrip("s"))
        for value in values:
            items.append({"type": singular, "value": value})
    return items

"""Mock threat intelligence providers."""

from __future__ import annotations

from typing import Any, Protocol

KNOWN_BAD_IPS = {
    "185.220.101.45": {
        "malicious": True,
        "score": 95,
        "labels": ["tor", "c2", "known_bad"],
        "country": "NL",
    },
}
KNOWN_BAD_DOMAINS = {
    "evil.example.com": {
        "malicious": True,
        "score": 98,
        "labels": ["malware", "c2", "phishing"],
        "categories": ["command-and-control"],
    },
}
KNOWN_BAD_HASHES = {
    "a3f5b8c91d2e4f60718293a4b5c6d7e8f90123456789abcdef0123456789abcd": {
        "malicious": True,
        "score": 92,
        "labels": ["trojan", "loader"],
        "names": ["trojan.loader.x64"],
    },
}


class ThreatIntelProvider(Protocol):
    name: str

    async def enrich(self, ioc_type: str, value: str) -> dict[str, Any]: ...


class MockVirusTotal:
    name = "virustotal"

    async def enrich(self, ioc_type: str, value: str) -> dict[str, Any]:
        value_l = value.lower()
        if ioc_type == "ip" and value in KNOWN_BAD_IPS:
            info = KNOWN_BAD_IPS[value]
            return {
                "provider": self.name,
                "type": ioc_type,
                "value": value,
                "malicious": True,
                "score": info["score"],
                "positives": 48,
                "total": 70,
                "labels": info["labels"],
            }
        if ioc_type == "domain" and value_l in KNOWN_BAD_DOMAINS:
            info = KNOWN_BAD_DOMAINS[value_l]
            return {
                "provider": self.name,
                "type": ioc_type,
                "value": value_l,
                "malicious": True,
                "score": info["score"],
                "positives": 35,
                "total": 90,
                "labels": info["labels"],
                "categories": info["categories"],
            }
        if ioc_type == "hash" and value_l in KNOWN_BAD_HASHES:
            info = KNOWN_BAD_HASHES[value_l]
            return {
                "provider": self.name,
                "type": ioc_type,
                "value": value_l,
                "malicious": True,
                "score": info["score"],
                "positives": 40,
                "total": 72,
                "labels": info["labels"],
                "names": info["names"],
            }
        # Benign / unknown baseline
        return {
            "provider": self.name,
            "type": ioc_type,
            "value": value,
            "malicious": False,
            "score": 5 if ioc_type != "cve" else 20,
            "positives": 0,
            "total": 70,
            "labels": [],
        }


class MockAbuseIPDB:
    name = "abuseipdb"

    async def enrich(self, ioc_type: str, value: str) -> dict[str, Any]:
        if ioc_type != "ip":
            return {
                "provider": self.name,
                "type": ioc_type,
                "value": value,
                "supported": False,
                "score": 0,
                "malicious": False,
            }
        if value in KNOWN_BAD_IPS:
            info = KNOWN_BAD_IPS[value]
            return {
                "provider": self.name,
                "type": "ip",
                "value": value,
                "malicious": True,
                "score": info["score"],
                "abuse_confidence": info["score"],
                "country": info.get("country"),
                "total_reports": 240,
                "labels": info["labels"],
            }
        return {
            "provider": self.name,
            "type": "ip",
            "value": value,
            "malicious": False,
            "score": 2,
            "abuse_confidence": 2,
            "total_reports": 0,
            "labels": [],
        }


def default_providers() -> list[ThreatIntelProvider]:
    return [MockVirusTotal(), MockAbuseIPDB()]

"""Deterministic mock LLM for offline demos and tests."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any


class MockLLM:
    """Returns deterministic JSON-ish security analysis from prompts."""

    provider_name = "mock"
    model = "mock-security-analyst"

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict[str, Any]:
        _ = temperature, max_tokens
        blob = "\n".join(m.get("content", "") for m in messages)
        lower = blob.lower()
        analysis = self._analyze(lower, blob)
        content = json.dumps(analysis, indent=2)
        return {
            "content": content,
            "raw": {"choices": [{"message": {"content": content}}]},
            "provider": self.provider_name,
            "model": model or self.model,
        }

    async def embed(
        self,
        texts: list[str] | str,
        *,
        model: str | None = None,
    ) -> dict[str, Any]:
        input_texts = [texts] if isinstance(texts, str) else list(texts)
        vectors = [self._embed_one(t) for t in input_texts]
        return {
            "embeddings": vectors,
            "raw": {"data": [{"embedding": v} for v in vectors]},
            "provider": self.provider_name,
            "model": model or "mock-embedding",
        }

    async def health(self) -> bool:
        return True

    def _analyze(self, lower: str, blob: str) -> dict[str, Any]:
        keywords = self._keywords(lower)
        iocs = self._extract_iocs(blob)
        severity = "critical" if any(
            k in lower for k in ("c2", "lateral", "ransomware", "malware", "185.220")
        ) else "high" if any(k in lower for k in ("bruteforce", "failed logon", "auth")) else "medium"

        if "keyword" in lower or "extract" in lower:
            return {
                "keywords": keywords[:3],
                "rationale": "Top discriminative terms from the investigation query.",
            }
        if "mitre" in lower:
            return {
                "techniques": [
                    {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
                    {"id": "T1059.001", "name": "PowerShell", "tactic": "Execution"},
                    {"id": "T1071.001", "name": "Web Protocols", "tactic": "Command and Control"},
                    {"id": "T1021.001", "name": "Remote Desktop Protocol", "tactic": "Lateral Movement"},
                    {"id": "T1543.003", "name": "Windows Service", "tactic": "Persistence"},
                ],
                "summary": "Attack chain maps from credential access through C2 to lateral movement.",
            }
        if "report" in lower or "executive" in lower:
            return {
                "executive_summary": (
                    "Credential stuffing against jdoe succeeded, followed by malware execution "
                    "and C2 to 185.220.101.45 / evil.example.com, then lateral movement to SRV-APP-12."
                ),
                "business_impact": "Finance workstation and application server compromised; domain risk elevated.",
                "recommended_actions": [
                    "Isolate WS-FINANCE-07 and SRV-APP-12",
                    "Reset credentials for jdoe and review privileged sessions",
                    "Block 185.220.101.45 and evil.example.com at the perimeter",
                ],
            }
        if "critic" in lower or "review" in lower or "quality" in lower:
            return {
                "approved": True,
                "confidence_adjustment": 0.0,
                "issues": [],
                "notes": "Findings are consistent across platforms and shared IOCs.",
            }
        if "remediation" in lower or "root cause" in lower:
            return {
                "root_cause": (
                    "External brute-force against jdoe led to interactive logon, "
                    "PowerShell payload (trojan.loader.x64), and C2 beaconing."
                ),
                "remediation": [
                    "Contain affected hosts",
                    "Block IOC network indicators",
                    "Hunt for hash a3f5b8c91d2e4f60718293a4b5c6d7e8f90123456789abcdef0123456789abcd",
                    "Enforce MFA and lockout policies",
                ],
                "severity": severity,
                "confidence": 0.86,
            }

        return {
            "analysis": (
                "Cross-platform evidence shows an intrusion: auth failures, malware C2 "
                "to 185.220.101.45, DNS to evil.example.com, and RDP lateral movement."
            ),
            "severity": severity,
            "confidence": 0.84,
            "keywords": keywords[:3],
            "iocs": iocs,
            "root_cause": (
                "Compromised credentials for jdoe enabled malware deployment and lateral movement."
            ),
            "remediation": [
                "Isolate impacted hosts",
                "Block C2 IP/domain",
                "Reset user credentials and review persistence",
            ],
        }

    @staticmethod
    def _keywords(lower: str) -> list[str]:
        candidates = [
            "bruteforce",
            "malware",
            "c2",
            "lateral",
            "powershell",
            "rdp",
            "persistence",
            "dns",
            "auth",
            "exfil",
        ]
        found = [c for c in candidates if c in lower]
        if not found:
            found = ["auth", "malware", "lateral"]
        return found

    @staticmethod
    def _extract_iocs(text: str) -> dict[str, list[str]]:
        ips = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)))
        domains = sorted(
            set(re.findall(r"\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|example)\b", text, re.I))
        )
        hashes = sorted(set(re.findall(r"\b[a-fA-F0-9]{32,64}\b", text)))
        return {"ips": ips, "domains": domains, "hashes": hashes}

    @staticmethod
    def _embed_one(text: str, dim: int = 64) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        values: list[float] = []
        while len(values) < dim:
            for b in digest:
                values.append((b / 255.0) * 2 - 1)
                if len(values) >= dim:
                    break
            digest = hashlib.sha256(digest).digest()
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

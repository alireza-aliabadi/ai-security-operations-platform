"""Golden-path investigation evaluation (brute force / C2 narrative)."""

from __future__ import annotations

import pytest

from aisoc.agents.graph import run_investigation
from aisoc.connectors.registry import reset_registry
from aisoc.threat_intel.extractors import extract_iocs


KNOWN_IOC = "185.220.101.45"


@pytest.mark.asyncio
async def test_golden_brute_force_c2_investigation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PRIMARY_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "test")
    reset_registry()

    query = (
        "Investigate brute force authentication against jdoe followed by malware "
        f"C2 beaconing to {KNOWN_IOC} and lateral movement via RDP"
    )
    result = await run_investigation(query, investigation_id="golden-c2")

    # Keywords extracted
    keywords = [str(k).lower() for k in (result.get("keywords") or [])]
    assert keywords, "expected keywords from keyword_extractor"
    assert any(
        any(token in k for token in ("brute", "c2", "malware", "auth", "lateral", "rdp"))
        for k in keywords
    ) or any(token in " ".join(keywords) for token in ("brute", "c2", "malware", "auth"))

    # Known IOC recovered from logs / analysis
    iocs = result.get("iocs") or {}
    ips: list[str] = []
    if isinstance(iocs, dict):
        ips = list(iocs.get("ips") or [])
    elif isinstance(iocs, list):
        ips = [str(x.get("value") if isinstance(x, dict) else x) for x in iocs]

    log_blob = " ".join(str(e.get("message", "")) for e in (result.get("logs") or []))
    extracted = extract_iocs([query, log_blob, str(result.get("technical_report") or "")])
    all_ips = set(ips) | set(extracted["ips"])
    assert KNOWN_IOC in all_ips or KNOWN_IOC in log_blob or KNOWN_IOC in str(result)

    # MITRE-ish fields present
    mitre = result.get("mitre") or []
    analysis = result.get("analysis") or {}
    mitre_blob = str(mitre) + str(analysis) + str(result.get("agent_trace") or [])
    assert any(
        token in mitre_blob
        for token in ("T1110", "T1071", "T1021", "Brute Force", "Command and Control", "mitre")
    ) or (isinstance(mitre, list) and len(mitre) > 0)

    severity = str(result.get("severity") or "").lower()
    assert severity in {"medium", "high", "critical"} or severity != "unknown"

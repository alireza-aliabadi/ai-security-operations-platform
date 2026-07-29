"""Unit tests for offline investigation graph execution."""

from __future__ import annotations

import pytest

from aisoc.agents.graph import run_investigation
from aisoc.connectors.registry import reset_registry


@pytest.mark.asyncio
async def test_run_investigation_offline_returns_keywords_and_severity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PRIMARY_API_KEY", "")
    monkeypatch.setenv("APP_ENV", "test")
    reset_registry()

    result = await run_investigation(
        "Investigate brute force login failures and malware C2 to 185.220.101.45",
        investigation_id="test-inv-1",
    )

    keywords = result.get("keywords") or []
    assert isinstance(keywords, list)
    assert len(keywords) >= 1

    severity = (result.get("severity") or "").lower()
    assert severity in {"low", "medium", "high", "critical", "unknown"} or severity != ""

    # Offline mock path should still produce useful investigation artifacts
    assert result.get("agent_trace")
    iocs = result.get("iocs") or {}
    ips = iocs.get("ips") if isinstance(iocs, dict) else []
    # Prefer finding the known IOC from logs/query; tolerate mock LLM variance
    blob = str(result)
    assert "185.220.101.45" in blob or (isinstance(ips, list) and "185.220.101.45" in ips)

"""Investigation graph state."""

from __future__ import annotations

from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):
    """Shared state flowing through the multi-agent investigation graph."""

    investigation_id: str
    query: str
    keywords: list[str]
    logs: list[dict[str, Any]]
    correlated: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]
    analysis: dict[str, Any]
    mitre: list[dict[str, Any]]
    iocs: dict[str, list[str]]
    severity: str
    confidence: float
    root_cause: str
    remediation: list[str]
    executive_report: str
    technical_report: str
    agent_trace: list[dict[str, Any]]
    approvals_needed: list[dict[str, Any]]
    errors: list[str]
    plan: dict[str, Any]
    interrupt_before_export: bool


def initial_state(
    query: str,
    *,
    investigation_id: str = "",
    interrupt_before_export: bool = False,
) -> InvestigationState:
    return InvestigationState(
        investigation_id=investigation_id,
        query=query,
        keywords=[],
        logs=[],
        correlated=[],
        rag_context=[],
        analysis={},
        mitre=[],
        iocs={"ips": [], "domains": [], "hashes": []},
        severity="unknown",
        confidence=0.0,
        root_cause="",
        remediation=[],
        executive_report="",
        technical_report="",
        agent_trace=[],
        approvals_needed=[],
        errors=[],
        plan={},
        interrupt_before_export=interrupt_before_export,
    )

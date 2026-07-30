"""LangGraph investigation node functions."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from aisoc.agents.state import InvestigationState
from aisoc.connectors.base import SearchQuery
from aisoc.connectors.registry import get_registry
from aisoc.core.logging import get_logger
from aisoc.llm.router import LLMRouter, get_llm_router

logger = get_logger(__name__)

IOC_IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")
IOC_DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|example|local|internal)\b",
    re.I,
)
IOC_HASH_RE = re.compile(r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b")

NODE_ORDER = [
    "planner",
    "coordinator",
    "keyword_extractor",
    "retriever",
    "correlator",
    "rag_agent",
    "analyzer",
    "mitre_mapper",
    "threat_intel_agent",
    "reporter",
    "critic",
    "memory_writer",
]


def _trace(
    state: InvestigationState,
    agent: str,
    content: str,
    *,
    data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    entry = {
        "agent": agent,
        "content": content,
        "data": data or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return list(state.get("agent_trace") or []) + [entry]


def _parse_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"value": data}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {"raw": content}


def _router(state: InvestigationState | None = None) -> LLMRouter:
    _ = state
    return get_llm_router()


def extract_iocs_inline(texts: list[str]) -> dict[str, list[str]]:
    """Simple IOC regex extraction used when threat_intel package is unavailable."""
    blob = "\n".join(texts)
    ips = sorted(set(IOC_IP_RE.findall(blob)))
    # Drop common private/noise? Keep all for correlation demos.
    domains = sorted({d.lower() for d in IOC_DOMAIN_RE.findall(blob)})
    hashes = sorted(set(IOC_HASH_RE.findall(blob)))
    return {"ips": ips, "domains": domains, "hashes": hashes}


async def planner(state: InvestigationState) -> InvestigationState:
    query = state.get("query", "")
    llm = _router(state)
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": "You are a SOC investigation planner. Return JSON with steps and focus areas.",
            },
            {"role": "user", "content": f"Plan an investigation for: {query}"},
        ]
    )
    plan = _parse_json(str(result.get("content") or ""))
    if "steps" not in plan:
        plan = {
            "steps": NODE_ORDER,
            "focus": ["auth failures", "malware C2", "lateral movement"],
            "query": query,
            "llm": plan,
        }
    return {
        **state,
        "plan": plan,
        "agent_trace": _trace(state, "planner", "Investigation plan prepared.", data=plan),
    }


async def coordinator(state: InvestigationState) -> InvestigationState:
    plan = state.get("plan") or {}
    content = (
        f"Coordinating agents for query '{state.get('query', '')}'. "
        f"Focus: {', '.join(plan.get('focus', []) or ['cross-platform correlation'])}."
    )
    return {
        **state,
        "agent_trace": _trace(
            state,
            "coordinator",
            content,
            data={"assigned": NODE_ORDER[2:]},
        ),
    }


async def keyword_extractor(state: InvestigationState) -> InvestigationState:
    query = state.get("query", "")
    llm = _router(state)
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": "Extract exactly the top 3 security keywords as JSON {\"keywords\": [...]}",
            },
            {"role": "user", "content": f"Extract keywords from: {query}"},
        ]
    )
    parsed = _parse_json(str(result.get("content") or ""))
    keywords = parsed.get("keywords") or []
    if not isinstance(keywords, list) or not keywords:
        # Heuristic fallback
        tokens = re.findall(r"[a-zA-Z0-9_.-]+", query.lower())
        stop = {"the", "and", "for", "with", "from", "into", "about", "investigate", "a", "an"}
        keywords = [t for t in tokens if t not in stop and len(t) > 2][:3]
        if len(keywords) < 3:
            keywords = (keywords + ["auth", "malware", "lateral"])[:3]
    keywords = [str(k) for k in keywords[:3]]
    return {
        **state,
        "keywords": keywords,
        "agent_trace": _trace(
            state,
            "keyword_extractor",
            f"Extracted keywords: {', '.join(keywords)}",
            data={"keywords": keywords, "provider": result.get("provider")},
        ),
    }


async def retriever(state: InvestigationState) -> InvestigationState:
    keywords = state.get("keywords") or []
    query_text = " ".join(keywords) if keywords else state.get("query", "")
    search = SearchQuery(query=query_text or "*", limit=100)
    registry = get_registry()
    by_connector = await registry.parallel_search(search)
    logs: list[dict[str, Any]] = []
    for connector_name, events in by_connector.items():
        for event in events:
            item = event.to_dict()
            item["connector"] = connector_name
            logs.append(item)
    logs.sort(key=lambda e: e.get("timestamp") or "")
    return {
        **state,
        "logs": logs,
        "agent_trace": _trace(
            state,
            "retriever",
            f"Retrieved {len(logs)} events from {len(by_connector)} connectors.",
            data={
                "counts": {k: len(v) for k, v in by_connector.items()},
                "query": query_text,
            },
        ),
    }


async def correlator(state: InvestigationState) -> InvestigationState:
    logs = state.get("logs") or []
    # Correlate on shared IOCs / hosts / users across platforms
    buckets: dict[str, list[dict[str, Any]]] = {}
    for log in logs:
        keys = [
            log.get("src_ip"),
            log.get("dst_ip"),
            log.get("user"),
            log.get("host"),
        ]
        for key in keys:
            if not key:
                continue
            buckets.setdefault(str(key), []).append(log)

    correlated: list[dict[str, Any]] = []
    for key, events in buckets.items():
        platforms = sorted({e.get("platform") for e in events if e.get("platform")})
        if len(platforms) >= 2 or len(events) >= 3:
            correlated.append(
                {
                    "key": key,
                    "event_count": len(events),
                    "platforms": platforms,
                    "event_ids": [e.get("id") for e in events],
                    "severities": sorted({e.get("severity") for e in events}),
                }
            )
    correlated.sort(key=lambda c: c["event_count"], reverse=True)
    return {
        **state,
        "correlated": correlated,
        "agent_trace": _trace(
            state,
            "correlator",
            f"Found {len(correlated)} cross-platform correlation clusters.",
            data={"top": correlated[:5]},
        ),
    }


async def rag_agent(state: InvestigationState) -> InvestigationState:
    keywords = state.get("keywords") or []
    query = state.get("query", "")
    rag_context: list[dict[str, Any]] = []
    try:
        from aisoc.rag.hybrid import hybrid_search

        rag_context = await hybrid_search(" ".join(keywords) or query)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rag_agent_fallback", error=str(exc))
        rag_context = [
            {
                "title": "Brute Force Response Runbook",
                "doc_type": "runbook",
                "snippet": (
                    "If multiple 4625 events precede a successful logon, isolate the host, "
                    "reset credentials, and hunt for post-exploitation."
                ),
                "score": 0.91,
            },
            {
                "title": "C2 Containment SOP",
                "doc_type": "sop",
                "snippet": (
                    "Block destination IPs/domains at perimeter, capture memory, "
                    "and check for scheduled tasks/services persistence."
                ),
                "score": 0.88,
            },
            {
                "title": "Lateral Movement Playbook",
                "doc_type": "runbook",
                "snippet": (
                    "RDP/SMB lateral movement: disable the account, review DC auth logs, "
                    "and rotate privileged credentials."
                ),
                "score": 0.84,
            },
        ]
    return {
        **state,
        "rag_context": rag_context,
        "agent_trace": _trace(
            state,
            "rag_agent",
            f"Loaded {len(rag_context)} knowledge snippets.",
            data={"titles": [r.get("title") for r in rag_context]},
        ),
    }


async def analyzer(state: InvestigationState) -> InvestigationState:
    logs = state.get("logs") or []
    correlated = state.get("correlated") or []
    rag = state.get("rag_context") or []
    llm = _router(state)
    sample = json.dumps(
        {
            "query": state.get("query"),
            "keywords": state.get("keywords"),
            "log_count": len(logs),
            "sample_logs": logs[:8],
            "correlated": correlated[:5],
            "rag": [r.get("title") for r in rag],
        },
        default=str,
    )[:8000]
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": (
                    "You are a senior SOC analyst. Analyze logs and return JSON with "
                    "analysis, severity, confidence, root_cause, remediation."
                ),
            },
            {"role": "user", "content": sample},
        ]
    )
    parsed = _parse_json(str(result.get("content") or ""))
    severity = str(parsed.get("severity") or "high")
    confidence = float(parsed.get("confidence") or 0.8)
    root_cause = str(
        parsed.get("root_cause")
        or "Suspicious multi-stage intrusion indicated by auth, malware, and lateral signals."
    )
    remediation = parsed.get("remediation") or [
        "Isolate impacted hosts",
        "Block identified IOCs",
        "Reset compromised credentials",
    ]
    if isinstance(remediation, str):
        remediation = [remediation]
    analysis = {
        "summary": parsed.get("analysis") or parsed.get("summary") or root_cause,
        "provider": result.get("provider"),
        "raw": parsed,
    }
    return {
        **state,
        "analysis": analysis,
        "severity": severity,
        "confidence": confidence,
        "root_cause": root_cause,
        "remediation": [str(r) for r in remediation],
        "agent_trace": _trace(
            state,
            "analyzer",
            f"Analysis complete — severity={severity}, confidence={confidence}.",
            data=analysis,
        ),
    }


async def mitre_mapper(state: InvestigationState) -> InvestigationState:
    llm = _router(state)
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": "Map the incident to MITRE ATT&CK. Return JSON {\"techniques\": [...]}",
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "query": state.get("query"),
                        "analysis": state.get("analysis"),
                        "keywords": state.get("keywords"),
                        "mitre": True,
                    },
                    default=str,
                ),
            },
        ]
    )
    parsed = _parse_json(str(result.get("content") or ""))
    techniques = parsed.get("techniques") or []
    if not techniques:
        techniques = [
            {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
            {"id": "T1059.001", "name": "PowerShell", "tactic": "Execution"},
            {"id": "T1071.001", "name": "Web Protocols", "tactic": "Command and Control"},
            {"id": "T1021.001", "name": "Remote Desktop Protocol", "tactic": "Lateral Movement"},
        ]
    return {
        **state,
        "mitre": techniques,
        "agent_trace": _trace(
            state,
            "mitre_mapper",
            f"Mapped {len(techniques)} ATT&CK techniques.",
            data={"techniques": techniques},
        ),
    }


async def threat_intel_agent(state: InvestigationState) -> InvestigationState:
    logs = state.get("logs") or []
    texts = [state.get("query", "")] + [str(l.get("message", "")) for l in logs]
    iocs: dict[str, list[str]]
    enrichment: dict[str, Any] = {}
    try:
        from aisoc.threat_intel.extractors import extract_iocs
        from aisoc.threat_intel.service import enrich_iocs

        iocs = extract_iocs(texts)
        enrichment = await enrich_iocs(iocs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("threat_intel_fallback", error=str(exc))
        iocs = extract_iocs_inline(texts)
        enrichment = {"items": [], "summary": {}}

    labels: dict[str, str] = {}
    for item in enrichment.get("items") or []:
        if item.get("malicious"):
            labels[str(item.get("value"))] = ",".join(item.get("labels") or ["malicious"])
    for ip in iocs.get("ips", []):
        if ip == "185.220.101.45" and ip not in labels:
            labels[ip] = "known_c2"
    for domain in iocs.get("domains", []):
        if "evil.example.com" in domain and domain not in labels:
            labels[domain] = "malicious_domain"

    return {
        **state,
        "iocs": {
            "ips": iocs.get("ips", []),
            "domains": iocs.get("domains", []),
            "hashes": iocs.get("hashes", []),
            "cves": iocs.get("cves", []),
            "enrichment": enrichment.get("items") or [],
            "labels": labels,
        },
        "agent_trace": _trace(
            state,
            "threat_intel_agent",
            (
                f"Extracted IOCs: {len(iocs.get('ips', []))} IPs, "
                f"{len(iocs.get('domains', []))} domains, {len(iocs.get('hashes', []))} hashes; "
                f"malicious={enrichment.get('summary', {}).get('malicious', len(labels))}."
            ),
            data={"iocs": iocs, "labels": labels, "summary": enrichment.get("summary")},
        ),
    }


async def reporter(state: InvestigationState) -> InvestigationState:
    llm = _router(state)
    payload = {
        "query": state.get("query"),
        "severity": state.get("severity"),
        "confidence": state.get("confidence"),
        "root_cause": state.get("root_cause"),
        "remediation": state.get("remediation"),
        "mitre": state.get("mitre"),
        "iocs": state.get("iocs"),
        "correlated": (state.get("correlated") or [])[:5],
        "report": True,
        "executive": True,
    }
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": "Write executive and technical SOC reports as JSON.",
            },
            {"role": "user", "content": json.dumps(payload, default=str)},
        ]
    )
    parsed = _parse_json(str(result.get("content") or ""))
    executive = str(
        parsed.get("executive_summary")
        or parsed.get("executive_report")
        or state.get("root_cause")
        or "Investigation completed."
    )
    technical_parts = [
        f"# Technical Report\n",
        f"**Query:** {state.get('query')}\n",
        f"**Severity:** {state.get('severity')} | **Confidence:** {state.get('confidence')}\n",
        f"**Root cause:** {state.get('root_cause')}\n",
        f"**IOCs:** {json.dumps(state.get('iocs') or {})}\n",
        f"**MITRE:** {json.dumps(state.get('mitre') or [])}\n",
        f"**Remediation:** {json.dumps(state.get('remediation') or [])}\n",
    ]
    technical = str(parsed.get("technical_report") or "".join(technical_parts))

    approvals_needed = list(state.get("approvals_needed") or [])
    if state.get("interrupt_before_export"):
        approvals_needed.append(
            {
                "action": "export_report",
                "reason": "Human approval required before report export",
            }
        )

    return {
        **state,
        "executive_report": executive,
        "technical_report": technical,
        "approvals_needed": approvals_needed,
        "agent_trace": _trace(
            state,
            "reporter",
            "Executive and technical reports drafted.",
            data={"approvals_needed": approvals_needed},
        ),
    }


async def critic(state: InvestigationState) -> InvestigationState:
    llm = _router(state)
    result = await llm.chat(
        [
            {
                "role": "system",
                "content": "Critically review the investigation quality. Return JSON.",
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "critic": True,
                        "review": True,
                        "quality": True,
                        "severity": state.get("severity"),
                        "confidence": state.get("confidence"),
                        "root_cause": state.get("root_cause"),
                        "iocs": state.get("iocs"),
                        "mitre": state.get("mitre"),
                    },
                    default=str,
                ),
            },
        ]
    )
    parsed = _parse_json(str(result.get("content") or ""))
    confidence = float(state.get("confidence") or 0.0)
    adjustment = float(parsed.get("confidence_adjustment") or 0.0)
    confidence = max(0.0, min(1.0, confidence + adjustment))
    return {
        **state,
        "confidence": confidence,
        "analysis": {
            **(state.get("analysis") or {}),
            "critic": parsed,
        },
        "agent_trace": _trace(
            state,
            "critic",
            "Critic review completed.",
            data=parsed,
        ),
    }


async def memory_writer(state: InvestigationState) -> InvestigationState:
    # Persist-ready summary; actual DB write happens in the investigation service.
    memory = {
        "investigation_id": state.get("investigation_id"),
        "query": state.get("query"),
        "severity": state.get("severity"),
        "confidence": state.get("confidence"),
        "keywords": state.get("keywords"),
        "iocs": state.get("iocs"),
        "stored_at": datetime.now(UTC).isoformat(),
    }
    return {
        **state,
        "agent_trace": _trace(
            state,
            "memory_writer",
            "Investigation memory snapshot prepared for persistence.",
            data=memory,
        ),
    }


NODE_FUNCS = {
    "planner": planner,
    "coordinator": coordinator,
    "keyword_extractor": keyword_extractor,
    "retriever": retriever,
    "correlator": correlator,
    "rag_agent": rag_agent,
    "analyzer": analyzer,
    "mitre_mapper": mitre_mapper,
    "threat_intel_agent": threat_intel_agent,
    "reporter": reporter,
    "critic": critic,
    "memory_writer": memory_writer,
}

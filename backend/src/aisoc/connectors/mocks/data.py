"""Deterministic mock security log corpus with shared IOCs across platforms."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

# Shared IOCs appearing across platforms for correlation demos
IOC_C2_IP = "185.220.101.45"
IOC_DOMAIN = "evil.example.com"
IOC_HASH = "a3f5b8c91d2e4f60718293a4b5c6d7e8f90123456789abcdef0123456789abcd"
IOC_MALWARE = "trojan.loader.x64"
IOC_USER = "jdoe"
IOC_HOST_WORKSTATION = "WS-FINANCE-07"
IOC_HOST_DC = "DC-01"
IOC_HOST_SERVER = "SRV-APP-12"

_BASE = datetime(2026, 7, 28, 8, 0, 0, tzinfo=UTC)


def _ts(minutes: int) -> datetime:
    return _BASE + timedelta(minutes=minutes)


def _event(
    *,
    eid: str,
    minutes: int,
    platform: str,
    index: str,
    source: str,
    message: str,
    severity: str = "info",
    host: str | None = None,
    user: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    process: str | None = None,
    tags: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": eid,
        "timestamp": _ts(minutes),
        "platform": platform,
        "index": index,
        "source": source,
        "message": message,
        "severity": severity,
        "host": host,
        "user": user,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "process": process,
        "tags": tags or [],
        "raw": extra,
    }


# ---------------------------------------------------------------------------
# Auth failure chain → malware C2 → lateral movement (shared narrative)
# ---------------------------------------------------------------------------

MOCK_EVENTS: list[dict[str, Any]] = [
    # --- Graylog: auth failures ---
    _event(
        eid="gl-001",
        minutes=0,
        platform="graylog",
        index="windows-security",
        source="WinEventLog:Security",
        message=f"Failed logon for user {IOC_USER} from 203.0.113.50 (EventID 4625)",
        severity="medium",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        src_ip="203.0.113.50",
        tags=["auth", "failure", "bruteforce"],
        event_id=4625,
        logon_type=3,
    ),
    _event(
        eid="gl-002",
        minutes=2,
        platform="graylog",
        index="windows-security",
        source="WinEventLog:Security",
        message=f"Failed logon for user {IOC_USER} from 203.0.113.50 (EventID 4625)",
        severity="medium",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        src_ip="203.0.113.50",
        tags=["auth", "failure", "bruteforce"],
        event_id=4625,
        logon_type=3,
    ),
    _event(
        eid="gl-003",
        minutes=5,
        platform="graylog",
        index="windows-security",
        source="WinEventLog:Security",
        message=f"Successful logon for user {IOC_USER} from 203.0.113.50 (EventID 4624)",
        severity="high",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        src_ip="203.0.113.50",
        tags=["auth", "success", "suspicious"],
        event_id=4624,
        logon_type=10,
    ),
    # --- Elasticsearch: process / malware ---
    _event(
        eid="es-001",
        minutes=12,
        platform="elasticsearch",
        index="endpoint-logs",
        source="elastic-agent",
        message=(
            f"Suspicious process powershell.exe spawned on {IOC_HOST_WORKSTATION} "
            f"downloading payload hash={IOC_HASH}"
        ),
        severity="high",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        process="powershell.exe",
        tags=["malware", "execution", "powershell"],
        file_hash=IOC_HASH,
        malware_family=IOC_MALWARE,
    ),
    _event(
        eid="es-002",
        minutes=15,
        platform="elasticsearch",
        index="endpoint-logs",
        source="elastic-agent",
        message=f"Outbound connection to C2 {IOC_C2_IP}:443 from {IOC_HOST_WORKSTATION}",
        severity="critical",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        src_ip="10.10.5.42",
        dst_ip=IOC_C2_IP,
        process="svchost.exe",
        tags=["c2", "network", "malware"],
        dest_port=443,
        protocol="tcp",
    ),
    # --- Loki: DNS / domain ---
    _event(
        eid="lk-001",
        minutes=14,
        platform="loki",
        index="dns",
        source="coredns",
        message=f"DNS query A {IOC_DOMAIN} from 10.10.5.42 answered {IOC_C2_IP}",
        severity="high",
        host=IOC_HOST_WORKSTATION,
        src_ip="10.10.5.42",
        dst_ip=IOC_C2_IP,
        tags=["dns", "c2", "ioc"],
        query_name=IOC_DOMAIN,
        query_type="A",
    ),
    _event(
        eid="lk-002",
        minutes=18,
        platform="loki",
        index="proxy",
        source="squid",
        message=f"HTTPS CONNECT {IOC_DOMAIN}:443 from {IOC_HOST_WORKSTATION} status=200",
        severity="high",
        host=IOC_HOST_WORKSTATION,
        src_ip="10.10.5.42",
        dst_ip=IOC_C2_IP,
        tags=["proxy", "c2", "exfil"],
        bytes_out=48210,
    ),
    # --- Splunk: lateral movement ---
    _event(
        eid="sp-001",
        minutes=25,
        platform="splunk",
        index="wineventlog",
        source="WinEventLog:Security",
        message=(
            f"Remote interactive logon {IOC_USER} on {IOC_HOST_SERVER} "
            f"from {IOC_HOST_WORKSTATION} (EventID 4624 LogonType 10)"
        ),
        severity="critical",
        host=IOC_HOST_SERVER,
        user=IOC_USER,
        src_ip="10.10.5.42",
        process="mstsc.exe",
        tags=["lateral", "rdp", "movement"],
        event_id=4624,
        logon_type=10,
    ),
    _event(
        eid="sp-002",
        minutes=28,
        platform="splunk",
        index="wineventlog",
        source="WinEventLog:Security",
        message=f"New service created on {IOC_HOST_SERVER} by {IOC_USER} (EventID 7045)",
        severity="critical",
        host=IOC_HOST_SERVER,
        user=IOC_USER,
        process="services.exe",
        tags=["persistence", "service", "lateral"],
        event_id=7045,
        service_name="WindowsUpdateHelper",
        service_path=f"C:\\Windows\\Temp\\{IOC_MALWARE}.exe",
    ),
    # --- OpenSearch: auth + network correlation ---
    _event(
        eid="os-001",
        minutes=3,
        platform="opensearch",
        index="security-audit",
        source="opensearch-security",
        message=f"Multiple failed authentications for {IOC_USER} threshold exceeded",
        severity="medium",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        src_ip="203.0.113.50",
        tags=["auth", "alert", "bruteforce"],
        failure_count=12,
    ),
    _event(
        eid="os-002",
        minutes=16,
        platform="opensearch",
        index="network-flow",
        source="zeek",
        message=f"Zeek conn: 10.10.5.42 -> {IOC_C2_IP}:443 bytes=51200 duration=90s",
        severity="high",
        host=IOC_HOST_WORKSTATION,
        src_ip="10.10.5.42",
        dst_ip=IOC_C2_IP,
        tags=["network", "c2", "zeek"],
        dest_port=443,
        bytes=51200,
    ),
    # --- Datadog: cloud / EDR ---
    _event(
        eid="dd-001",
        minutes=13,
        platform="datadog",
        index="security-signals",
        source="datadog-agent",
        message=(
            f"Threat detected: {IOC_MALWARE} on {IOC_HOST_WORKSTATION} "
            f"file_hash={IOC_HASH} contacting {IOC_DOMAIN}"
        ),
        severity="critical",
        host=IOC_HOST_WORKSTATION,
        user=IOC_USER,
        dst_ip=IOC_C2_IP,
        process="powershell.exe",
        tags=["malware", "edr", "datadog"],
        signal_id="sig-malware-001",
        file_hash=IOC_HASH,
    ),
    _event(
        eid="dd-002",
        minutes=30,
        platform="datadog",
        index="security-signals",
        source="datadog-agent",
        message=(
            f"Lateral movement detected: {IOC_USER} authenticated to {IOC_HOST_DC} "
            f"via {IOC_HOST_SERVER} using compromised session"
        ),
        severity="critical",
        host=IOC_HOST_DC,
        user=IOC_USER,
        src_ip="10.10.20.12",
        tags=["lateral", "domain", "kerberos"],
        signal_id="sig-lateral-002",
    ),
    # Additional noise / benign for filtering demos
    _event(
        eid="gl-100",
        minutes=1,
        platform="graylog",
        index="syslog",
        source="sshd",
        message="Accepted publickey for deploy from 10.0.0.5 port 52222",
        severity="info",
        host="bastion-01",
        user="deploy",
        src_ip="10.0.0.5",
        tags=["auth", "success"],
    ),
    _event(
        eid="es-100",
        minutes=20,
        platform="elasticsearch",
        index="endpoint-logs",
        source="elastic-agent",
        message="Scheduled task Microsoft Compatibility Appraiser completed successfully",
        severity="info",
        host="WS-HR-02",
        user="SYSTEM",
        process="CompatTelRunner.exe",
        tags=["benign", "scheduled"],
    ),
    _event(
        eid="sp-100",
        minutes=10,
        platform="splunk",
        index="application",
        source="iis",
        message="GET /health 200 12ms",
        severity="info",
        host="web-01",
        tags=["http", "health"],
        status=200,
    ),
]


SHARED_IOCS: dict[str, str] = {
    "c2_ip": IOC_C2_IP,
    "domain": IOC_DOMAIN,
    "file_hash": IOC_HASH,
    "malware": IOC_MALWARE,
    "user": IOC_USER,
}


def events_for_platform(platform: str) -> list[dict[str, Any]]:
    return [e for e in MOCK_EVENTS if e["platform"] == platform]


def all_indices_for_platform(platform: str) -> list[str]:
    return sorted({e["index"] for e in events_for_platform(platform)})

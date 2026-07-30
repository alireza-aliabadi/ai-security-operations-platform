"""Unit tests for IOC extraction."""

from __future__ import annotations

from aisoc.threat_intel.extractors import extract_iocs, flatten_iocs


SAMPLE = """
Failed auth then malware beacon to 185.220.101.45 and evil.example.com.
Hash a3f5b8c91d2e4f60718293a4b5c6d7e8f90123456789abcdef0123456789abcd
Related CVE-2024-3400 observed on perimeter.
"""


def test_extract_iocs_includes_known_c2_ip() -> None:
    iocs = extract_iocs(SAMPLE)
    assert "185.220.101.45" in iocs["ips"]
    assert "evil.example.com" in iocs["domains"]
    assert any(h.lower().startswith("a3f5") for h in iocs["hashes"])
    assert "CVE-2024-3400" in iocs["cves"]


def test_flatten_iocs() -> None:
    items = flatten_iocs(extract_iocs(SAMPLE))
    types = {i["type"] for i in items}
    values = {i["value"] for i in items}
    assert "ip" in types
    assert "185.220.101.45" in values

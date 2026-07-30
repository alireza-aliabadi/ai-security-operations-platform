"""AISOC MCP server exposing SOC investigation tools over stdio."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from aisoc_mcp.client import BackendClient
from aisoc_mcp.config import get_settings

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_logs",
        "description": "Search logs across connected platforms (Graylog, ES, Loki, Splunk, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "default": "*"},
                "platforms": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 100},
            },
        },
    },
    {
        "name": "search_indices",
        "description": "Search specific indices/streams for a query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "indices": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 100},
            },
            "required": ["query", "indices"],
        },
    },
    {
        "name": "query_platform",
        "description": "Run a search against a single platform connector.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "platform": {"type": "string"},
                "limit": {"type": "integer", "default": 100},
            },
            "required": ["query", "platform"],
        },
    },
    {
        "name": "aggregate",
        "description": "Aggregate log field values across platforms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "default": "*"},
                "field": {"type": "string", "default": "severity"},
                "size": {"type": "integer", "default": 10},
                "platforms": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "timeline",
        "description": "Build a cross-platform event timeline for a query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "default": "*"},
                "platforms": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 100},
            },
        },
    },
    {
        "name": "incident_summary",
        "description": "Fetch executive/technical summary for an investigation.",
        "inputSchema": {
            "type": "object",
            "properties": {"investigation_id": {"type": "string"}},
            "required": ["investigation_id"],
        },
    },
    {
        "name": "lookup_ioc",
        "description": "Enrich an IOC (IP, domain, hash, CVE) via threat intelligence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "type": {"type": "string", "description": "ip|domain|hash|cve"},
                "text": {"type": "string", "description": "Free text to extract+enrich"},
            },
        },
    },
    {
        "name": "knowledge_search",
        "description": "Hybrid RAG search over security knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8},
                "doc_type": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "runbook_search",
        "description": "Search security runbooks in the knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8},
            },
            "required": ["query"],
        },
    },
]


async def dispatch_tool(client: BackendClient, name: str, arguments: dict[str, Any]) -> Any:
    if name == "search_logs":
        return await client.search_logs(
            arguments.get("query", "*"),
            platforms=arguments.get("platforms"),
            limit=int(arguments.get("limit") or 100),
        )
    if name == "search_indices":
        return await client.search_indices(
            arguments["query"],
            list(arguments.get("indices") or []),
            limit=int(arguments.get("limit") or 100),
        )
    if name == "query_platform":
        return await client.query_platform(
            arguments["query"],
            arguments["platform"],
            limit=int(arguments.get("limit") or 100),
        )
    if name == "aggregate":
        return await client.aggregate(
            arguments.get("query", "*"),
            field=arguments.get("field", "severity"),
            size=int(arguments.get("size") or 10),
            platforms=arguments.get("platforms"),
        )
    if name == "timeline":
        return await client.timeline(
            arguments.get("query", "*"),
            platforms=arguments.get("platforms"),
            limit=int(arguments.get("limit") or 100),
        )
    if name == "incident_summary":
        return await client.incident_summary(arguments["investigation_id"])
    if name == "lookup_ioc":
        return await client.lookup_ioc(
            str(arguments.get("value") or ""),
            ioc_type=arguments.get("type"),
            text=arguments.get("text"),
        )
    if name == "knowledge_search":
        return await client.knowledge_search(
            arguments["query"],
            limit=int(arguments.get("limit") or 8),
            doc_type=arguments.get("doc_type"),
        )
    if name == "runbook_search":
        return await client.runbook_search(
            arguments["query"],
            limit=int(arguments.get("limit") or 8),
        )
    raise ValueError(f"Unknown tool: {name}")


def _run_fastmcp() -> bool:
    """Run using the official MCP Python SDK FastMCP."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return False

    settings = get_settings()
    mcp = FastMCP("aisoc", host=settings.mcp_host, port=settings.mcp_port)
    client = BackendClient(settings)

    @mcp.tool()
    async def search_logs(
        query: str = "*",
        platforms: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Search logs across connected platforms."""
        return await client.search_logs(query, platforms=platforms, limit=limit)

    @mcp.tool()
    async def search_indices(query: str, indices: list[str], limit: int = 100) -> dict[str, Any]:
        """Search specific indices/streams."""
        return await client.search_indices(query, indices, limit=limit)

    @mcp.tool()
    async def query_platform(query: str, platform: str, limit: int = 100) -> dict[str, Any]:
        """Query a single platform connector."""
        return await client.query_platform(query, platform, limit=limit)

    @mcp.tool()
    async def aggregate(
        query: str = "*",
        field: str = "severity",
        size: int = 10,
        platforms: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate a field across platforms."""
        return await client.aggregate(query, field=field, size=size, platforms=platforms)

    @mcp.tool()
    async def timeline(
        query: str = "*",
        platforms: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Build a cross-platform timeline."""
        return await client.timeline(query, platforms=platforms, limit=limit)

    @mcp.tool()
    async def incident_summary(investigation_id: str) -> dict[str, Any]:
        """Fetch an investigation report summary."""
        return await client.incident_summary(investigation_id)

    @mcp.tool()
    async def lookup_ioc(
        value: str = "",
        type: str | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """Enrich an IOC via threat intelligence."""
        return await client.lookup_ioc(value, ioc_type=type, text=text)

    @mcp.tool()
    async def knowledge_search(
        query: str,
        limit: int = 8,
        doc_type: str | None = None,
    ) -> dict[str, Any]:
        """Hybrid RAG knowledge search."""
        return await client.knowledge_search(query, limit=limit, doc_type=doc_type)

    @mcp.tool()
    async def runbook_search(query: str, limit: int = 8) -> dict[str, Any]:
        """Search security runbooks."""
        return await client.runbook_search(query, limit=limit)

    mcp.run(transport=settings.mcp_transport)
    return True


class StdioJSONRPCServer:
    """Minimal MCP-compatible JSON-RPC server over stdio."""

    def __init__(self) -> None:
        self.client = BackendClient()
        self._id = 0

    def _write(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        sys.stdout.write(payload + "\n")
        sys.stdout.flush()

    def _result(self, req_id: Any, result: Any) -> None:
        self._write({"jsonrpc": "2.0", "id": req_id, "result": result})

    def _error(self, req_id: Any, code: int, message: str) -> None:
        self._write(
            {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        )

    async def handle(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        req_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            self._result(
                req_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aisoc", "version": "0.1.0"},
                },
            )
            return
        if method == "notifications/initialized":
            return
        if method == "tools/list":
            self._result(req_id, {"tools": TOOL_DEFINITIONS})
            return
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                result = await dispatch_tool(self.client, str(name), dict(arguments))
                self._result(
                    req_id,
                    {
                        "content": [
                            {"type": "text", "text": json.dumps(result, indent=2, default=str)}
                        ]
                    },
                )
            except Exception as exc:  # noqa: BLE001
                self._error(req_id, -32000, str(exc))
            return
        if method == "ping":
            self._result(req_id, {})
            return
        if req_id is not None:
            self._error(req_id, -32601, f"Method not found: {method}")

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            await self.handle(message)
        await self.client.close()


def main() -> None:
    settings = get_settings()
    if _run_fastmcp():
        return
    if settings.mcp_transport != "stdio":
        raise RuntimeError(
            f"MCP transport {settings.mcp_transport!r} requires the mcp SDK (FastMCP)"
        )
    asyncio.run(StdioJSONRPCServer().run())


if __name__ == "__main__":
    main()

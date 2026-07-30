# AISOC MCP Server

Exposes AI Security Operations Platform capabilities as Model Context Protocol tools.

## Tools

| Tool | Description |
|------|-------------|
| `search_logs` | Cross-platform log search |
| `search_indices` | Search specific indices/streams |
| `query_platform` | Query a single connector platform |
| `aggregate` | Aggregate a field across platforms |
| `timeline` | Cross-platform event timeline |
| `incident_summary` | Investigation report summary |
| `lookup_ioc` | Threat intel IOC enrichment |
| `knowledge_search` | Hybrid RAG knowledge search |
| `runbook_search` | Runbook-only knowledge search |

## Configuration

Environment variables:

- `BACKEND_INTERNAL_URL` — AISOC API base URL (default `http://localhost:8000`)
- `MCP_API_TOKEN` — Bearer token accepted by the backend (must match backend `MCP_API_TOKEN`)

## Run

```bash
cd mcp-server
poetry install
export BACKEND_INTERNAL_URL=http://localhost:8000
export MCP_API_TOKEN=mcp-dev-token-change-me
poetry run aisoc-mcp
```

The server speaks MCP over **stdio**. Prefer the official `mcp` Python SDK (`FastMCP`) when installed; otherwise a small JSON-RPC stdio fallback is used.

## Cursor / Claude Desktop example

```json
{
  "mcpServers": {
    "aisoc": {
      "command": "poetry",
      "args": ["-C", "/path/to/mcp-server", "run", "aisoc-mcp"],
      "env": {
        "BACKEND_INTERNAL_URL": "http://localhost:8000",
        "MCP_API_TOKEN": "mcp-dev-token-change-me"
      }
    }
  }
}
```

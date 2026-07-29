"""MCP server configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

MCPTransport = Literal["stdio", "sse", "streamable-http"]


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_internal_url: str = "http://localhost:8000"
    mcp_api_token: str = "mcp-dev-token-change-me"
    request_timeout: float = 60.0
    mcp_transport: MCPTransport = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8100


@lru_cache
def get_settings() -> MCPSettings:
    return MCPSettings()

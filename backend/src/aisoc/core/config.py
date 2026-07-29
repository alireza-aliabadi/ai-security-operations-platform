"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Security Operations Platform"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    secret_key: str = Field(min_length=32)
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    seed_admin_email: str = "admin@aisoc.local"
    seed_admin_password: str = "ChangeMeAdmin123!"
    seed_analyst_email: str = "analyst@aisoc.local"
    seed_analyst_password: str = "ChangeMeAnalyst123!"

    database_url: str = "postgresql+psycopg://aisoc:aisoc_secret@localhost:5432/aisoc"
    database_url_sync: str = "postgresql+psycopg://aisoc:aisoc_secret@localhost:5432/aisoc"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "aisoc_knowledge"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    oidc_enabled: bool = True
    oidc_issuer: str = "http://localhost:8080/realms/aisoc"
    oidc_client_id: str = "aisoc-frontend"
    oidc_client_secret: str = "aisoc-oidc-secret"
    oidc_redirect_uri: str = "http://localhost:5173/auth/callback"

    llm_primary_base_url: str = "https://api.openai.com/v1"
    llm_primary_api_key: str = ""
    llm_primary_model: str = "gpt-4o-mini"
    llm_local_base_url: str = "http://localhost:11434/v1"
    llm_local_api_key: str = "ollama"
    llm_local_model: str = "llama3.2"
    llm_fallback_order: str = "primary,local,mock"
    llm_embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"

    connector_mode: Literal["mock", "live"] = "mock"
    encryption_key: str = "0123456789abcdef0123456789abcdef"

    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "aisoc-api"
    prometheus_enabled: bool = True

    mcp_api_token: str = "mcp-dev-token-change-me"
    backend_internal_url: str = "http://localhost:8000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: object) -> object:
        if isinstance(value, str):
            import json

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @property
    def llm_providers(self) -> list[str]:
        return [p.strip() for p in self.llm_fallback_order.split(",") if p.strip()]

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

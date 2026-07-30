"""Secrets vault stub — EnvVault backend reading from environment / settings."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger

logger = get_logger(__name__)


class VaultClient(ABC):
    """Abstract secrets vault interface."""

    @abstractmethod
    async def get_secret(self, key: str, default: str | None = None) -> str | None: ...

    @abstractmethod
    async def set_secret(self, key: str, value: str) -> None: ...

    @abstractmethod
    async def delete_secret(self, key: str) -> bool: ...

    @abstractmethod
    async def list_secrets(self, prefix: str = "") -> list[str]: ...


class EnvVault(VaultClient):
    """
    Development vault backed by process environment and optional in-memory overrides.

    Looks up secrets as:
      1. In-memory overrides (set via set_secret)
      2. Environment variables (KEY or AISOC_SECRET_KEY)
      3. Known settings attributes (snake_case)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._overrides: dict[str, str] = {}

    def _env_names(self, key: str) -> list[str]:
        upper = key.upper().replace(".", "_").replace("-", "_")
        return [upper, f"AISOC_SECRET_{upper}", f"AISOC_{upper}"]

    async def get_secret(self, key: str, default: str | None = None) -> str | None:
        if key in self._overrides:
            return self._overrides[key]
        for name in self._env_names(key):
            if name in os.environ:
                return os.environ[name]
        # Map common keys onto Settings fields
        attr = key.lower().replace("-", "_")
        if hasattr(self.settings, attr):
            value = getattr(self.settings, attr)
            if value is not None and not callable(value):
                return str(value)
        return default

    async def set_secret(self, key: str, value: str) -> None:
        self._overrides[key] = value
        logger.info("vault_secret_set", key=key)

    async def delete_secret(self, key: str) -> bool:
        existed = key in self._overrides
        self._overrides.pop(key, None)
        return existed

    async def list_secrets(self, prefix: str = "") -> list[str]:
        keys = set(self._overrides)
        for name in os.environ:
            if name.startswith("AISOC_SECRET_"):
                keys.add(name.removeprefix("AISOC_SECRET_").lower())
        if prefix:
            keys = {k for k in keys if k.startswith(prefix)}
        return sorted(keys)


_vault: VaultClient | None = None


def get_vault(settings: Settings | None = None) -> VaultClient:
    global _vault
    if _vault is None:
        _vault = EnvVault(settings=settings)
    return _vault


async def get_secret(key: str, default: str | None = None) -> str | None:
    return await get_vault().get_secret(key, default)

"""Marketplace preparado (repositorio remoto, firma, versionado)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class RemotePluginInfo:
    name: str
    version: str
    description: str
    url: str
    signature: str | None = None
    checksum: str | None = None


class PluginRepository(Protocol):
    """Contrato para un marketplace remoto futuro."""

    def search(self, query: str) -> list[RemotePluginInfo]: ...

    def fetch(self, name: str, version: str | None = None) -> bytes: ...

    def verify(self, payload: bytes, signature: str | None) -> bool: ...


class StubMarketplace:
    """Placeholder: lista vacía hasta conectar un repo real."""

    name = "stub"

    def search(self, query: str) -> list[RemotePluginInfo]:
        return []

    def fetch(self, name: str, version: str | None = None) -> bytes:
        raise NotImplementedError(
            "Marketplace remoto aún no configurado. "
            "Instala plugins locales con: jarvis plugins install ./ruta/plugin"
        )

    def verify(self, payload: bytes, signature: str | None) -> bool:
        return signature is None

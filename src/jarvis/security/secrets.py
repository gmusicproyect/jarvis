"""Secret Manager — Keychain / Credential Manager / env."""

from __future__ import annotations

import os
from typing import Protocol

from jarvis.platform import PlatformName, detect_platform
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.security.secrets")

SERVICE = "jarvis-assistant"


class SecretStore(Protocol):
    def get(self, key: str) -> str | None: ...

    def set(self, key: str, value: str) -> None: ...

    def delete(self, key: str) -> None: ...


class EnvSecretStore:
    """Fallback: variables de entorno (no escribe secretos a disco)."""

    name = "env"

    def get(self, key: str) -> str | None:
        env_key = key.upper().replace(".", "_").replace("-", "_")
        return os.getenv(env_key) or os.getenv(f"JARVIS_{env_key}")

    def set(self, key: str, value: str) -> None:
        env_key = key.upper().replace(".", "_").replace("-", "_")
        os.environ[env_key] = value
        _LOG.info("secret_set_env", key=env_key)

    def delete(self, key: str) -> None:
        env_key = key.upper().replace(".", "_").replace("-", "_")
        os.environ.pop(env_key, None)
        os.environ.pop(f"JARVIS_{env_key}", None)


class MacKeychainStore:
    name = "keychain"

    def get(self, key: str) -> str | None:
        import subprocess

        try:
            out = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-a",
                    key,
                    "-s",
                    SERVICE,
                    "-w",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return out.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def set(self, key: str, value: str) -> None:
        import subprocess

        # borrar previo
        subprocess.run(
            ["security", "delete-generic-password", "-a", key, "-s", SERVICE],
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a",
                key,
                "-s",
                SERVICE,
                "-w",
                value,
            ],
            check=True,
            capture_output=True,
        )
        _LOG.info("secret_set_keychain", key=key)

    def delete(self, key: str) -> None:
        import subprocess

        subprocess.run(
            ["security", "delete-generic-password", "-a", key, "-s", SERVICE],
            check=False,
            capture_output=True,
        )


class WindowsCredentialStore:
    """Stub preparado para Windows Credential Manager."""

    name = "windows_credential"

    def get(self, key: str) -> str | None:
        return EnvSecretStore().get(key)

    def set(self, key: str, value: str) -> None:
        # Fase futura: keyring / win32cred
        EnvSecretStore().set(key, value)
        _LOG.warning("windows_credential_stub_using_env", key=key)

    def delete(self, key: str) -> None:
        EnvSecretStore().delete(key)


def get_secret_store() -> SecretStore:
    platform = detect_platform()
    if platform == PlatformName.MACOS:
        return MacKeychainStore()
    if platform == PlatformName.WINDOWS:
        return WindowsCredentialStore()
    return EnvSecretStore()


class SecretManager:
    def __init__(self, store: SecretStore | None = None) -> None:
        self.store = store or get_secret_store()

    def get(self, key: str, default: str | None = None) -> str | None:
        # Preferir store seguro; fallback env
        value = self.store.get(key)
        if value:
            return value
        return EnvSecretStore().get(key) or default

    def set(self, key: str, value: str) -> None:
        self.store.set(key, value)

    def delete(self, key: str) -> None:
        self.store.delete(key)

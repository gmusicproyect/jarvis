"""Abstracción de plataforma (macOS / Windows / Linux)."""

from __future__ import annotations

import sys
from enum import Enum
from typing import Protocol

from jarvis.utils.logging import get_logger


class PlatformName(str, Enum):
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"


def detect_platform() -> PlatformName:
    if sys.platform == "darwin":
        return PlatformName.MACOS
    if sys.platform == "win32":
        return PlatformName.WINDOWS
    if sys.platform.startswith("linux"):
        return PlatformName.LINUX
    return PlatformName.UNKNOWN


class OSAdapter(Protocol):
    """Contrato legacy — preferir AutomationEngine en Fase 5+."""

    name: PlatformName

    def open_url(self, url: str) -> None: ...

    def open_app(self, app_name: str) -> None: ...


class _MacOSAdapter:
    name = PlatformName.MACOS

    def open_url(self, url: str) -> None:
        import subprocess

        subprocess.run(["open", url], check=True)

    def open_app(self, app_name: str) -> None:
        from jarvis.automation.macos import MacApplicationController

        MacApplicationController().open_app(app_name)


def get_os_adapter() -> OSAdapter:
    """Factory ligera; la automatización completa usa ``build_automation_engine``."""
    platform = detect_platform()
    if platform == PlatformName.MACOS:
        return _MacOSAdapter()
    get_logger("jarvis.platform").warning("os_adapter_limited", platform=platform.value)
    raise NotImplementedError(
        f"OS adapter completo para {platform.value} llega con AutomationEngine stubs"
    )

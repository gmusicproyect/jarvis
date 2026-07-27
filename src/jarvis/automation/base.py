"""Contratos del Automation Engine — proveedores intercambiables."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class PermissionLevel(int, Enum):
    """Niveles de permiso (1=seguro, 2=confirmación, 3=restringido)."""

    SAFE = 1
    CONFIRM = 2
    RESTRICTED = 3


@dataclass
class ActionRequest:
    action: str
    description: str
    level: PermissionLevel
    params: dict[str, Any] = field(default_factory=dict)
    user_name: str = "Juan"
    dry_run: bool = False


@dataclass
class ActionResult:
    success: bool
    message: str
    action: str
    level: PermissionLevel
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    elapsed_ms: float = 0.0
    confirmed: bool | None = None
    cancelled: bool = False


@runtime_checkable
class ApplicationController(Protocol):
    name: str

    def open_app(self, app_name: str) -> None: ...

    def close_app(self, app_name: str) -> None: ...

    def is_running(self, app_name: str) -> bool: ...


@runtime_checkable
class BrowserController(Protocol):
    name: str

    def open_url(self, url: str) -> None: ...

    def search_google(self, query: str) -> None: ...

    def click(self, selector: str) -> None: ...

    def fill(self, selector: str, text: str) -> None: ...

    def get_page_text(self) -> str: ...

    def extract_tables(self) -> list[list[list[str]]]: ...

    def screenshot(self, path: Path) -> Path: ...

    def download(self, url: str, dest: Path) -> Path: ...

    def close(self) -> None: ...


@runtime_checkable
class FileController(Protocol):
    name: str

    def open_path(self, path: Path) -> None: ...

    def open_folder(self, path: Path) -> None: ...

    def find(self, name: str, root: Path | None = None) -> list[Path]: ...

    def move(self, src: Path, dest: Path) -> Path: ...

    def copy(self, src: Path, dest: Path) -> Path: ...

    def rename(self, src: Path, new_name: str) -> Path: ...

    def trash(self, path: Path) -> None: ...

    def delete_permanent(self, path: Path) -> None: ...


@runtime_checkable
class ClipboardController(Protocol):
    name: str

    def read(self) -> str: ...

    def write(self, text: str) -> None: ...


@runtime_checkable
class WindowController(Protocol):
    name: str

    def list_windows(self) -> list[str]: ...

    def focus(self, title_or_app: str) -> None: ...

    def minimize(self, title_or_app: str | None = None) -> None: ...


@runtime_checkable
class KeyboardController(Protocol):
    name: str

    def type_text(self, text: str) -> None: ...

    def hotkey(self, *keys: str) -> None: ...


@runtime_checkable
class MouseController(Protocol):
    name: str

    def click(self, x: int, y: int, button: str = "left") -> None: ...

    def move(self, x: int, y: int) -> None: ...


@runtime_checkable
class ShellController(Protocol):
    name: str

    def run(self, command: str, *, allowed: bool = False) -> tuple[int, str, str]: ...


@runtime_checkable
class ScreenshotController(Protocol):
    name: str

    def capture(self, path: Path | None = None) -> Path: ...

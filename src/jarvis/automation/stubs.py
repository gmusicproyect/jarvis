"""Stubs multiplataforma (Windows/Linux) hasta implementación completa."""

from __future__ import annotations

from pathlib import Path


class _NotReady:
    def __getattr__(self, item: str):  # noqa: ANN001
        def _fn(*args, **kwargs):  # noqa: ANN001, ANN002
            raise NotImplementedError(
                f"Controlador '{item}' no implementado en esta plataforma aún."
            )

        return _fn


class StubControllers:
    def __init__(self) -> None:
        self.apps = _AppStub()
        self.files = _FileStub()
        self.clipboard = _ClipboardStub()
        self.windows = _NotReady()
        self.keyboard = _NotReady()
        self.mouse = _NotReady()
        self.shell = _ShellStub()
        self.screenshot = _NotReady()


class _AppStub:
    name = "stub_app"

    def open_app(self, app_name: str) -> None:
        raise NotImplementedError(f"open_app({app_name}) pendiente en esta plataforma")

    def close_app(self, app_name: str) -> None:
        raise NotImplementedError

    def is_running(self, app_name: str) -> bool:
        return False


class _FileStub:
    name = "stub_file"

    def open_path(self, path: Path) -> None:
        raise NotImplementedError

    def open_folder(self, path: Path) -> None:
        raise NotImplementedError

    def find(self, name: str, root: Path | None = None) -> list[Path]:
        return []

    def move(self, src: Path, dest: Path) -> Path:
        raise NotImplementedError

    def copy(self, src: Path, dest: Path) -> Path:
        raise NotImplementedError

    def rename(self, src: Path, new_name: str) -> Path:
        raise NotImplementedError

    def trash(self, path: Path) -> None:
        raise NotImplementedError

    def delete_permanent(self, path: Path) -> None:
        raise NotImplementedError


class _ClipboardStub:
    name = "stub_clipboard"
    _buf: str = ""

    def read(self) -> str:
        return self._buf

    def write(self, text: str) -> None:
        self._buf = text


class _ShellStub:
    name = "stub_shell"

    def run(self, command: str, *, allowed: bool = False) -> tuple[int, str, str]:
        raise NotImplementedError

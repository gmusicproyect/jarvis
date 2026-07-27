"""AutomationEngine — orquesta controladores + permisos + auditoría."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jarvis.automation.audit import AutomationAudit
from jarvis.automation.base import (
    ActionRequest,
    ActionResult,
    ApplicationController,
    BrowserController,
    ClipboardController,
    FileController,
    KeyboardController,
    MouseController,
    PermissionLevel,
    ScreenshotController,
    ShellController,
    WindowController,
)
from jarvis.automation.gate import PermissionGate
from jarvis.utils.logging import get_logger


class AutomationEngine:
    """Fachada segura sobre los controladores del sistema operativo."""

    def __init__(
        self,
        *,
        apps: ApplicationController,
        browser: BrowserController,
        files: FileController,
        clipboard: ClipboardController,
        windows: WindowController,
        keyboard: KeyboardController,
        mouse: MouseController,
        shell: ShellController,
        screenshot: ScreenshotController,
        gate: PermissionGate,
        audit: AutomationAudit,
        user_name: str = "Juan",
        cancel_flag: list[bool] | None = None,
    ) -> None:
        self.apps = apps
        self.browser = browser
        self.files = files
        self.clipboard = clipboard
        self.windows = windows
        self.keyboard = keyboard
        self.mouse = mouse
        self.shell = shell
        self.screenshot = screenshot
        self.gate = gate
        self.audit = audit
        self.user_name = user_name
        self._cancel = cancel_flag if cancel_flag is not None else [False]
        self._log = get_logger("jarvis.automation")
        self._pending: tuple[ActionRequest, Callable[[], ActionResult]] | None = None

    def set_cancel_flag(self, flag: list[bool]) -> None:
        self._cancel = flag

    def cancel_pending(self) -> None:
        self._pending = None
        self._cancel[0] = True

    def confirm_pending(self) -> ActionResult | None:
        if not self._pending:
            return None
        request, runner = self._pending
        self._pending = None
        return self._execute(request, runner, confirmed=True)

    def run(
        self,
        action: str,
        description: str,
        level: PermissionLevel,
        runner: Callable[[], ActionResult],
        *,
        confirmed: bool = False,
        params: dict[str, Any] | None = None,
    ) -> ActionResult:
        request = ActionRequest(
            action=action,
            description=description,
            level=level,
            params=params or {},
            user_name=self.user_name,
        )
        blocked = self.gate.authorize(request, confirmed=confirmed)
        if blocked is not None:
            if blocked.data.get("needs_confirm"):
                self._pending = (request, runner)
            self.audit.record(request, blocked)
            return blocked
        return self._execute(request, runner, confirmed=confirmed)

    def _execute(
        self,
        request: ActionRequest,
        runner: Callable[[], ActionResult],
        *,
        confirmed: bool,
    ) -> ActionResult:
        if self._cancel[0]:
            self._cancel[0] = False
            result = ActionResult(
                success=False,
                message="Acción cancelada.",
                action=request.action,
                level=request.level,
                cancelled=True,
                confirmed=confirmed,
            )
            self.audit.record(request, result)
            return result

        self._log.info(
            "automation_start",
            action=request.action,
            description=request.description,
            level=request.level.value,
        )
        t0 = time.perf_counter()
        try:
            result = runner()
            result.elapsed_ms = (time.perf_counter() - t0) * 1000
            result.confirmed = confirmed if request.level != PermissionLevel.SAFE else None
            result.action = request.action
            result.level = request.level
        except Exception as exc:  # noqa: BLE001
            result = ActionResult(
                success=False,
                message=f"Error en {request.action}: {exc}",
                action=request.action,
                level=request.level,
                error=str(exc),
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                confirmed=confirmed,
            )
        self.audit.record(request, result)
        return result

    # --- helpers de alto nivel ---

    def open_application(self, app_name: str, *, confirmed: bool = False) -> ActionResult:
        def _run() -> ActionResult:
            self.apps.open_app(app_name)
            return ActionResult(
                True,
                f"Abriendo {app_name}.",
                "open_application",
                PermissionLevel.SAFE,
                data={"app": app_name},
            )

        return self.run(
            "open_application",
            f"Abrir aplicación «{app_name}»",
            PermissionLevel.SAFE,
            _run,
            confirmed=confirmed,
            params={"app": app_name},
        )

    def open_url(self, url: str, *, confirmed: bool = False) -> ActionResult:
        def _run() -> ActionResult:
            self.browser.open_url(url)
            return ActionResult(
                True,
                f"Abriendo {url}.",
                "open_url",
                PermissionLevel.SAFE,
                data={"url": url},
            )

        return self.run(
            "open_url",
            f"Abrir URL {url}",
            PermissionLevel.SAFE,
            _run,
            confirmed=confirmed,
            params={"url": url},
        )

    def find_and_open(self, name: str, root: Path | None = None) -> ActionResult:
        def _run() -> ActionResult:
            hits = self.files.find(name, root)
            if not hits:
                return ActionResult(
                    False,
                    f"No encontré «{name}».",
                    "find_and_open",
                    PermissionLevel.SAFE,
                )
            path = hits[0]
            self.files.open_path(path)
            return ActionResult(
                True,
                f"Encontré y abrí {path}.",
                "find_and_open",
                PermissionLevel.SAFE,
                data={"path": str(path), "candidates": [str(h) for h in hits[:5]]},
            )

        return self.run(
            "find_and_open",
            f"Buscar y abrir «{name}»",
            PermissionLevel.SAFE,
            _run,
            params={"name": name},
        )

    def trash_file(self, path: Path, *, confirmed: bool = False) -> ActionResult:
        def _run() -> ActionResult:
            self.files.trash(path)
            return ActionResult(
                True,
                f"Envié {path} a la papelera.",
                "trash_file",
                PermissionLevel.CONFIRM,
                data={"path": str(path)},
            )

        return self.run(
            "trash_file",
            f"Enviar a la papelera: {path}",
            PermissionLevel.CONFIRM,
            _run,
            confirmed=confirmed,
            params={"path": str(path)},
        )

    def clipboard_write(self, text: str) -> ActionResult:
        def _run() -> ActionResult:
            self.clipboard.write(text)
            return ActionResult(
                True,
                "Texto copiado al portapapeles.",
                "clipboard_write",
                PermissionLevel.SAFE,
                data={"chars": len(text)},
            )

        return self.run(
            "clipboard_write",
            "Escribir en el portapapeles",
            PermissionLevel.SAFE,
            _run,
        )

    def clipboard_read(self) -> ActionResult:
        def _run() -> ActionResult:
            text = self.clipboard.read()
            preview = text[:120] + ("…" if len(text) > 120 else "")
            return ActionResult(
                True,
                f"Portapapeles: {preview}" if text else "El portapapeles está vacío.",
                "clipboard_read",
                PermissionLevel.SAFE,
                data={"text": text},
            )

        return self.run(
            "clipboard_read",
            "Leer el portapapeles",
            PermissionLevel.SAFE,
            _run,
        )

    def take_screenshot(self, path: Path | None = None) -> ActionResult:
        def _run() -> ActionResult:
            out = self.screenshot.capture(path)
            return ActionResult(
                True,
                f"Captura guardada en {out}.",
                "screenshot",
                PermissionLevel.SAFE,
                data={"path": str(out)},
            )

        return self.run(
            "screenshot",
            "Tomar captura de pantalla",
            PermissionLevel.SAFE,
            _run,
        )

    def type_text(self, text: str, *, confirmed: bool = False) -> ActionResult:
        def _run() -> ActionResult:
            self.keyboard.type_text(text)
            return ActionResult(
                True,
                "Texto escrito.",
                "type_text",
                PermissionLevel.CONFIRM,
                data={"chars": len(text)},
            )

        return self.run(
            "type_text",
            f"Escribir texto automáticamente ({len(text)} caracteres)",
            PermissionLevel.CONFIRM,
            _run,
            confirmed=confirmed,
        )

    def run_shell(self, command: str, *, confirmed: bool = False) -> ActionResult:
        # comandos peligrosos → RESTRICTED
        low = command.lower()
        level = PermissionLevel.CONFIRM
        if any(x in low for x in ("rm ", "sudo", "chmod", "chown", "kill", "diskutil")):
            level = PermissionLevel.RESTRICTED

        def _run() -> ActionResult:
            code, out, err = self.shell.run(command)
            ok = code == 0
            msg = (out or err or f"exit {code}").strip()[:400]
            return ActionResult(
                ok,
                msg or f"Comando terminó con código {code}.",
                "shell",
                level,
                data={"code": code, "stdout": out, "stderr": err},
                error=err if not ok else None,
            )

        return self.run(
            "shell",
            f"Ejecutar comando: {command}",
            level,
            _run,
            confirmed=confirmed,
            params={"command": command},
        )

    def focus_window(self, title_or_app: str) -> ActionResult:
        def _run() -> ActionResult:
            self.windows.focus(title_or_app)
            return ActionResult(
                True,
                f"Foco en {title_or_app}.",
                "focus_window",
                PermissionLevel.SAFE,
                data={"target": title_or_app},
            )

        return self.run(
            "focus_window",
            f"Cambiar foco a «{title_or_app}»",
            PermissionLevel.SAFE,
            _run,
        )

    def rename_file(
        self, src: Path, new_name: str, *, confirmed: bool = False
    ) -> ActionResult:
        def _run() -> ActionResult:
            dest = self.files.rename(src, new_name)
            return ActionResult(
                True,
                f"Renombrado a {dest.name}.",
                "rename_file",
                PermissionLevel.CONFIRM,
                data={"path": str(dest)},
            )

        return self.run(
            "rename_file",
            f"Renombrar {src.name} → {new_name}",
            PermissionLevel.CONFIRM,
            _run,
            confirmed=confirmed,
        )

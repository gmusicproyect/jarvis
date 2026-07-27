"""Captura de pantalla — macOS screencapture + stubs."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from jarvis.platform import PlatformName, detect_platform
from jarvis.vision.base import CaptureMode, ScreenCapture
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.vision.screen")


class MacScreenProvider:
    name = "macos_screencapture"

    def capture_full(self, dest: Path) -> ScreenCapture:
        return self._capture(dest, CaptureMode.FULL, ["screencapture", "-x", str(dest)])

    def capture_active_window(self, dest: Path) -> ScreenCapture:
        # -l captura la ventana con foco (window id); -w interactivo.
        # Usamos -l con id de ventana frontal vía AppleScript.
        wid = self._front_window_id()
        if wid:
            return self._capture(
                dest,
                CaptureMode.ACTIVE_WINDOW,
                ["screencapture", "-x", "-l", str(wid), str(dest)],
            )
        # fallback: pantalla completa
        _LOG.warning("active_window_id_missing_fallback_full")
        return self.capture_full(dest)

    def capture_region(
        self, dest: Path, region: tuple[int, int, int, int]
    ) -> ScreenCapture:
        x, y, w, h = region
        # screencapture -R x,y,w,h
        cap = self._capture(
            dest,
            CaptureMode.REGION,
            ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", str(dest)],
        )
        cap.region = region
        return cap

    def capture_monitor(self, dest: Path, monitor: int) -> ScreenCapture:
        # -D <display> (1-based en macOS recientes)
        cap = self._capture(
            dest,
            CaptureMode.MONITOR,
            ["screencapture", "-x", "-D", str(monitor), str(dest)],
        )
        cap.monitor = monitor
        return cap

    def _front_window_id(self) -> int | None:
        script = (
            'tell application "System Events" to get id of first window '
            "of (first process whose frontmost is true)"
        )
        try:
            out = subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            return int(out) if out.isdigit() else None
        except Exception:  # noqa: BLE001
            return None

    def _capture(
        self, dest: Path, mode: CaptureMode, cmd: list[str]
    ) -> ScreenCapture:
        dest = dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            _LOG.error(
                "screencapture_failed",
                mode=mode.value,
                error=exc.stderr or str(exc),
            )
            raise RuntimeError(
                "No se pudo capturar la pantalla. Concede permiso de "
                "Grabación de pantalla a Terminal/Cursor en Ajustes del Sistema."
            ) from exc
        if not dest.exists() or dest.stat().st_size == 0:
            raise RuntimeError(f"Captura vacía: {dest}")
        elapsed = (time.perf_counter() - t0) * 1000
        _LOG.info(
            "screen_captured",
            mode=mode.value,
            path=str(dest),
            elapsed_ms=round(elapsed, 1),
        )
        return ScreenCapture(path=dest, mode=mode, elapsed_ms=elapsed)


class StubScreenProvider:
    name = "stub_screen"

    def capture_full(self, dest: Path) -> ScreenCapture:
        raise NotImplementedError("Captura de pantalla no disponible en esta plataforma")

    def capture_active_window(self, dest: Path) -> ScreenCapture:
        raise NotImplementedError

    def capture_region(
        self, dest: Path, region: tuple[int, int, int, int]
    ) -> ScreenCapture:
        raise NotImplementedError

    def capture_monitor(self, dest: Path, monitor: int) -> ScreenCapture:
        raise NotImplementedError


def build_screen_provider() -> MacScreenProvider | StubScreenProvider:
    if detect_platform() == PlatformName.MACOS:
        return MacScreenProvider()
    return StubScreenProvider()

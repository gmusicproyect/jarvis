"""GUI — Fase 7.

La interfaz nunca contiene lógica de negocio: consume ``JarvisGuiController``.
Shell actual: PySide6. Sustituible vía contrato ``GuiShell``.
"""

from __future__ import annotations


def run_gui(backend: str = "qt") -> int:
    """Arranca la interfaz gráfica."""
    if backend in {"qt", "pyside6", "pyside"}:
        from jarvis.gui.qt.app import run_qt_gui

        return run_qt_gui()
    if backend in {"web", "tauri"}:
        raise NotImplementedError(
            f"Backend GUI '{backend}' previsto para fases futuras. Usa backend=qt."
        )
    raise ValueError(f"Backend GUI desconocido: {backend}")


__all__ = ["run_gui"]

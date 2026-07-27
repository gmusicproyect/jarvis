"""Arranque de la shell Qt (PySide6)."""

from __future__ import annotations

import sys

from jarvis.gui.api.controller import JarvisGuiController
from jarvis.gui.qt.styles import JARVIS_QSS


def run_qt_gui() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError as exc:
        print(
            "PySide6 no está instalado.\n"
            "  poetry install -E gui\n"
            "  poetry run jarvis gui",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    from jarvis.gui.qt.main_window import MainWindow
    from jarvis.gui.qt.tray import TrayController
    from jarvis.onboarding import needs_onboarding, run_onboarding

    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(JARVIS_QSS)

    if needs_onboarding():
        reply = QMessageBox.question(
            None,
            "Bienvenido a Jarvis",
            "Hola, soy Jarvis. ¿Quieres el asistente de configuración inicial?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            run_onboarding(non_interactive=True, skip_backup=False)

    controller = JarvisGuiController()
    window = MainWindow(controller)
    tray = TrayController(app, controller, window)
    _ = tray
    if controller.cfg.gui.start_minimized:
        window.hide()
    else:
        window.show()
    return app.exec()

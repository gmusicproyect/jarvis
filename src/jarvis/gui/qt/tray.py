"""Bandeja del sistema y notificaciones nativas."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from jarvis.gui.api.controller import JarvisGuiController
from jarvis.gui.qt.main_window import MainWindow


def _jarvis_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(QColor("#1a1d23"))
    painter = QPainter(pix)
    painter.setBrush(QColor("#c9a227"))
    painter.setPen(QColor("#c9a227"))
    painter.drawEllipse(8, 8, 48, 48)
    painter.setPen(QColor("#1a1d23"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(22)
    painter.setFont(font)
    painter.drawText(pix.rect(), int(Qt.AlignmentFlag.AlignCenter), "J")
    painter.end()
    return QIcon(pix)


class TrayController:
    def __init__(self, app: QApplication, controller: JarvisGuiController, window: MainWindow) -> None:
        self.app = app
        self.ctrl = controller
        self.window = window
        self.tray = QSystemTrayIcon(_jarvis_icon(), app)
        self.tray.setToolTip("Jarvis")
        menu = QMenu()
        act_show = QAction("Abrir ventana", menu)
        act_show.triggered.connect(self._show)
        act_start = QAction("Iniciar Jarvis", menu)
        act_start.triggered.connect(lambda: self.ctrl.start_voice())
        act_stop = QAction("Detener Jarvis", menu)
        act_stop.triggered.connect(lambda: self.ctrl.stop_voice())
        act_mic = QAction("Activar/desactivar micrófono", menu)
        act_mic.triggered.connect(
            lambda: self.ctrl.set_mic_enabled(not self.ctrl.status().mic_enabled)
        )
        act_cfg = QAction("Configuración", menu)
        act_cfg.triggered.connect(self.window.show_settings_tab)
        act_logs = QAction("Ver logs recientes", menu)
        act_logs.triggered.connect(self.window.show_logs_dialog)
        act_quit = QAction("Salir", menu)
        act_quit.triggered.connect(self._quit)
        for a in (act_show, act_start, act_stop, act_mic, act_cfg, act_logs, act_quit):
            menu.addAction(a)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)
        self.tray.show()
        self.ctrl.set_notifier(self.notify)

    def notify(self, title: str, message: str, level: str = "info") -> None:
        icon = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
        }.get(level, QSystemTrayIcon.MessageIcon.Information)
        self.tray.showMessage(title, message, icon, 4000)

    def _show(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show()

    def _quit(self) -> None:
        self.ctrl.stop_voice()
        self.app.quit()

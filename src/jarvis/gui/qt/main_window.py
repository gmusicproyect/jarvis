"""Ventana principal PySide6."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from jarvis.gui.api.controller import JarvisGuiController
from jarvis.gui.api.models import ConfigForm, ConversationTurn, StatusSnapshot


class MainWindow(QMainWindow):
    def __init__(self, controller: JarvisGuiController) -> None:
        super().__init__()
        self.ctrl = controller
        self.setWindowTitle("Jarvis")
        self.resize(1100, 720)
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_all)
        self._timer.start(2000)
        self.refresh_all()

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        header = QHBoxLayout()
        title = QLabel("Jarvis")
        title.setObjectName("title")
        subtitle = QLabel("Asistente local-first · panel de control")
        subtitle.setObjectName("subtitle")
        head_col = QVBoxLayout()
        head_col.addWidget(title)
        head_col.addWidget(subtitle)
        header.addLayout(head_col)
        header.addStretch()
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.setObjectName("primary")
        self.btn_stop = QPushButton("Detener")
        self.btn_mic = QPushButton("Micrófono")
        self.btn_start.clicked.connect(self._start)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_mic.clicked.connect(self._toggle_mic)
        header.addWidget(self.btn_start)
        header.addWidget(self.btn_stop)
        header.addWidget(self.btn_mic)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_status_tab(), "Estado")
        self.tabs.addTab(self._build_chat_tab(), "Conversación")
        self.tabs.addTab(self._build_config_tab(), "Configuración")
        self.tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._build_release_tab(), "Release")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _build_status_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.status_list = QListWidget()
        lay.addWidget(self.status_list)
        metrics = QHBoxLayout()
        self.lbl_cpu = QLabel("CPU: —")
        self.lbl_ram = QLabel("RAM: —")
        self.lbl_lat = QLabel("Latencia: —")
        self.lbl_last = QLabel("Última: —")
        for lbl in (self.lbl_cpu, self.lbl_ram, self.lbl_lat, self.lbl_last):
            metrics.addWidget(lbl)
        lay.addLayout(metrics)
        return w

    def _build_chat_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.chat_view = QPlainTextEdit()
        self.chat_view.setReadOnly(True)
        lay.addWidget(self.chat_view)
        row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Escribe a Jarvis…")
        self.chat_input.returnPressed.connect(self._send_chat)
        send = QPushButton("Enviar")
        send.setObjectName("primary")
        send.clicked.connect(self._send_chat)
        row.addWidget(self.chat_input)
        row.addWidget(send)
        lay.addLayout(row)
        return w

    def _build_config_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        form = QFormLayout()
        self.cfg_llm = QLineEdit()
        self.cfg_llm_provider = QComboBox()
        self.cfg_llm_provider.addItems(["ollama", "openai", "anthropic"])
        self.cfg_vision_provider = QComboBox()
        self.cfg_vision_provider.addItems(["ollama", "openai", "gemini", "stub"])
        self.cfg_vision_model = QLineEdit()
        self.cfg_ocr = QComboBox()
        self.cfg_ocr.addItems(["tesseract", "easyocr", "stub"])
        self.cfg_voice = QLineEdit()
        self.cfg_lang = QLineEdit()
        self.cfg_wake = QLineEdit()
        self.cfg_wake_thr = QDoubleSpinBox()
        self.cfg_wake_thr.setRange(0.05, 0.99)
        self.cfg_wake_thr.setSingleStep(0.05)
        self.cfg_volume = QDoubleSpinBox()
        self.cfg_volume.setRange(0.5, 2.0)
        self.cfg_volume.setSingleStep(0.1)
        self.cfg_knowledge = QLineEdit()
        self.cfg_chunk = QSpinBox()
        self.cfg_chunk.setRange(100, 4000)
        self.cfg_overlap = QSpinBox()
        self.cfg_overlap.setRange(0, 1000)
        self.cfg_topk = QSpinBox()
        self.cfg_topk.setRange(1, 20)
        self.cfg_browser = QComboBox()
        self.cfg_browser.addItems(["system_open", "playwright"])

        form.addRow("Proveedor LLM", self.cfg_llm_provider)
        form.addRow("Modelo LLM", self.cfg_llm)
        form.addRow("Proveedor visión", self.cfg_vision_provider)
        form.addRow("Modelo visión", self.cfg_vision_model)
        form.addRow("OCR", self.cfg_ocr)
        form.addRow("Voz TTS", self.cfg_voice)
        form.addRow("Idioma", self.cfg_lang)
        form.addRow("Wake Word", self.cfg_wake)
        form.addRow("Sensibilidad wake", self.cfg_wake_thr)
        form.addRow("Velocidad TTS", self.cfg_volume)
        form.addRow("Carpeta conocimiento", self.cfg_knowledge)
        form.addRow("RAG chunk", self.cfg_chunk)
        form.addRow("RAG overlap", self.cfg_overlap)
        form.addRow("RAG top_k", self.cfg_topk)
        form.addRow("Navegador", self.cfg_browser)
        lay.addLayout(form)
        save = QPushButton("Guardar configuración")
        save.setObjectName("primary")
        save.clicked.connect(self._save_config)
        lay.addWidget(save)
        lay.addStretch()
        self._load_config_form()
        return w

    def _build_dashboard_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        def box(title: str) -> tuple[QGroupBox, QListWidget]:
            g = QGroupBox(title)
            l = QVBoxLayout(g)
            lst = QListWidget()
            l.addWidget(lst)
            return g, lst

        g1, self.dash_memory = box("Memoria")
        g2, self.dash_docs = box("Documentos RAG")
        g3, self.dash_skills = box("Skills usadas")
        g4, self.dash_auto = box("Automatizaciones")
        g5, self.dash_vision = box("Historial visión")
        g6, self.dash_audit = box("Auditoría")

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.addWidget(g1)
        ll.addWidget(g2)
        ll.addWidget(g3)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.addWidget(g4)
        rl.addWidget(g5)
        rl.addWidget(g6)
        splitter.addWidget(left)
        splitter.addWidget(right)
        lay.addWidget(splitter)
        return w

    def _build_release_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        from jarvis import __version__
        from jarvis.profiles import current_profile_name, list_profiles

        lay.addWidget(QLabel(f"Jarvis {__version__} — Release Candidate"))
        lay.addWidget(QLabel(f"Perfil activo: {current_profile_name()}"))

        row = QHBoxLayout()
        self.profile_combo = QComboBox()
        for name, desc in list_profiles():
            self.profile_combo.addItem(f"{name} — {desc}", name)
        # select current
        cur = current_profile_name()
        for i in range(self.profile_combo.count()):
            if self.profile_combo.itemData(i) == cur:
                self.profile_combo.setCurrentIndex(i)
                break
        btn_profile = QPushButton("Aplicar perfil")
        btn_profile.clicked.connect(self._apply_profile_gui)
        row.addWidget(self.profile_combo)
        row.addWidget(btn_profile)
        lay.addLayout(row)

        btn_doctor = QPushButton("Ejecutar doctor")
        btn_doctor.setObjectName("primary")
        btn_doctor.clicked.connect(self._run_doctor_gui)
        lay.addWidget(btn_doctor)

        self.doctor_view = QPlainTextEdit()
        self.doctor_view.setReadOnly(True)
        self.doctor_view.setPlaceholderText("Resultado de jarvis doctor…")
        lay.addWidget(self.doctor_view)

        priv = QHBoxLayout()
        btn_export = QPushButton("Exportar mis datos")
        btn_export.clicked.connect(self._export_privacy_gui)
        btn_wipe = QPushButton("Borrar memoria")
        btn_wipe.clicked.connect(self._wipe_privacy_gui)
        priv.addWidget(btn_export)
        priv.addWidget(btn_wipe)
        lay.addLayout(priv)
        return w

    def _apply_profile_gui(self) -> None:
        from jarvis.profiles import apply_profile

        name = self.profile_combo.currentData()
        apply_profile(str(name))
        QMessageBox.information(self, "Jarvis", f"Perfil «{name}» aplicado.")
        self.refresh_all()

    def _run_doctor_gui(self) -> None:
        from jarvis.config import clear_config_cache, get_config
        from jarvis.doctor import format_report, run_doctor

        clear_config_cache()
        report = run_doctor(get_config())
        self.doctor_view.setPlainText(format_report(report))

    def _export_privacy_gui(self) -> None:
        from jarvis.config import get_config
        from jarvis.privacy import export_personal_data

        path = export_personal_data(get_config())
        QMessageBox.information(self, "Jarvis", f"Exportado:\n{path}")

    def _wipe_privacy_gui(self) -> None:
        from jarvis.config import get_config
        from jarvis.privacy import wipe_all_memory

        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Borrar toda la memoria personal? Esta acción no se puede deshacer.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        stats = wipe_all_memory(get_config(), keep_user_name=True)
        QMessageBox.information(
            self,
            "Jarvis",
            f"Memoria borrada ({stats['sqlite_items']} ítems).",
        )

    def _load_config_form(self) -> None:
        f = self.ctrl.get_config_form()
        self.cfg_llm.setText(f.llm_model)
        self.cfg_llm_provider.setCurrentText(f.llm_provider)
        self.cfg_vision_provider.setCurrentText(f.vision_provider)
        self.cfg_vision_model.setText(f.vision_model)
        self.cfg_ocr.setCurrentText(f.ocr_provider)
        self.cfg_voice.setText(f.tts_voice)
        self.cfg_lang.setText(f.language)
        self.cfg_wake.setText(f.wake_model)
        self.cfg_wake_thr.setValue(f.wake_threshold)
        self.cfg_volume.setValue(f.volume)
        self.cfg_knowledge.setText(f.knowledge_dir)
        self.cfg_chunk.setValue(f.rag_chunk_size)
        self.cfg_overlap.setValue(f.rag_chunk_overlap)
        self.cfg_topk.setValue(f.rag_top_k)
        self.cfg_browser.setCurrentText(f.browser_provider)

    def _save_config(self) -> None:
        form = ConfigForm(
            llm_model=self.cfg_llm.text().strip(),
            llm_provider=self.cfg_llm_provider.currentText(),
            vision_provider=self.cfg_vision_provider.currentText(),
            vision_model=self.cfg_vision_model.text().strip(),
            ocr_provider=self.cfg_ocr.currentText(),
            tts_voice=self.cfg_voice.text().strip(),
            language=self.cfg_lang.text().strip() or "es",
            wake_model=self.cfg_wake.text().strip(),
            wake_threshold=float(self.cfg_wake_thr.value()),
            volume=float(self.cfg_volume.value()),
            knowledge_dir=self.cfg_knowledge.text().strip() or "knowledge",
            rag_chunk_size=int(self.cfg_chunk.value()),
            rag_chunk_overlap=int(self.cfg_overlap.value()),
            rag_top_k=int(self.cfg_topk.value()),
            browser_provider=self.cfg_browser.currentText(),
        )
        msg = self.ctrl.apply_config_form(form)
        QMessageBox.information(self, "Jarvis", msg)
        self.refresh_all()

    def _start(self) -> None:
        self.status_bar.showMessage(self.ctrl.start_voice())
        self.refresh_all()

    def _stop(self) -> None:
        self.status_bar.showMessage(self.ctrl.stop_voice())
        self.refresh_all()

    def _toggle_mic(self) -> None:
        self.ctrl.set_mic_enabled(not self.ctrl.status().mic_enabled)
        self.refresh_all()

    def _send_chat(self) -> None:
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._append_turn(ConversationTurn(role="user", text=text))
        turn = self.ctrl.ask_text(text)
        self._append_turn(turn)
        self.refresh_all()

    def _append_turn(self, turn: ConversationTurn) -> None:
        meta = []
        if turn.elapsed_ms is not None:
            meta.append(f"{turn.elapsed_ms:.0f} ms")
        if turn.skill:
            meta.append(f"skill:{turn.skill}")
        if turn.sources:
            meta.append("RAG: " + ", ".join(turn.sources[:3]))
        if turn.error:
            meta.append(f"error: {turn.error}")
        suffix = f"  ({' · '.join(meta)})" if meta else ""
        who = {"user": "Tú", "jarvis": "Jarvis", "error": "Error", "system": "Sistema"}.get(
            turn.role, turn.role
        )
        self.chat_view.appendPlainText(f"{who}: {turn.text}{suffix}\n")

    def show_settings_tab(self) -> None:
        self.tabs.setCurrentIndex(2)
        self.show()
        self.raise_()
        self.activateWindow()

    def show_logs_dialog(self) -> None:
        logs = "\n".join(self.ctrl.recent_logs())
        box = QMessageBox(self)
        box.setWindowTitle("Logs recientes")
        box.setText(logs[-4000:] if len(logs) > 4000 else logs)
        box.exec()

    def refresh_all(self) -> None:
        snap = self.ctrl.status()
        self._paint_status(snap)
        self._paint_dashboard()
        # sync chat from controller if voice produced turns
        # (simple: only append missing by recount — keep local chat for typed)

    def _paint_status(self, snap: StatusSnapshot) -> None:
        self.status_list.clear()
        state = "EN MARCHA" if snap.running else "DETENIDO"
        self.status_list.addItem(f"Estado general: {state}")
        for m in snap.modules:
            mark = "●" if m.ok else "○"
            self.status_list.addItem(f"{mark} {m.name}: {m.detail}")
        self.lbl_cpu.setText(
            f"CPU: {snap.cpu_percent:.0f}%" if snap.cpu_percent is not None else "CPU: —"
        )
        self.lbl_ram.setText(
            f"RAM: {snap.ram_mb:.0f} MB" if snap.ram_mb is not None else "RAM: —"
        )
        self.lbl_lat.setText(
            f"Latencia: {snap.avg_latency_ms:.0f} ms"
            if snap.avg_latency_ms is not None
            else "Latencia: —"
        )
        self.lbl_last.setText(f"Última: {snap.last_interaction}")
        self.btn_mic.setText("Micrófono ON" if snap.mic_enabled else "Micrófono OFF")
        self.status_bar.showMessage(
            f"{snap.user_name} · LLM {snap.llm} · Visión {snap.vision} · Ollama {snap.ollama}"
        )

    def _paint_dashboard(self) -> None:
        data = self.ctrl.dashboard()

        def fill(widget: QListWidget, rows: list[str]) -> None:
            widget.clear()
            for r in rows or ["(vacío)"]:
                widget.addItem(r)

        fill(self.dash_memory, data.memory_notes)
        fill(self.dash_docs, data.indexed_docs)
        fill(
            self.dash_skills,
            [f"{n}: {c}" for n, c in data.top_skills] or ["(sin uso aún)"],
        )
        fill(self.dash_auto, data.automations)
        fill(self.dash_vision, data.vision_history)
        fill(self.dash_audit, data.audit_rows)

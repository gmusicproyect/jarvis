# Roadmap y plan por fases

## Roadmap (visión)

| Fase | Nombre | Resultado |
|------|--------|-----------|
| 0 | Cimientos | Poetry, config, logging, árbol, legacy aislado |
| 1 | Voz cerrada | Wake → STT → Ollama/n8n → TTS (paridad con `jarvis_pro`) |
| 2 | Memoria | SQLite short/long + personalidad por nombre |
| 3 | Skills base | Abrir apps/URLs, archivos, calculadora, timer |
| 4 | RAG | Indexar carpeta docs + responder con citas |
| 5 | Automation OS | macOS completo + esqueleto Windows |
| 6 | Vision | OCR, screenshot, leer pantalla |
| 7 | GUI | Tray + panel estado/historial |
| 8 | Hardening | Seguridad, tests ≥80%, installers, cutover |
| 9 | Release Candidate | v1.0.0-rc · doctor · onboarding · DMG |
| 10 | Multiagente _(futuro)_ | Roles especializados |

---

## Fase 0 — Cimientos (1–2 sesiones)

- [ ] `pyproject.toml` Poetry
- [ ] `config/config.yaml` + `.env.example` + loader tipado (Pydantic)
- [ ] `src/jarvis/` esqueleto de paquetes
- [ ] Mover scripts actuales a `legacy/`
- [ ] Logging profesional a `data/logs/`
- [ ] `python -m jarvis --version` / healthcheck
- [ ] Docs ya creadas en `docs/`

**Criterio de salida:** proyecto instalable con Poetry; legacy sigue funcionando.

## Fase 1 — Paridad de voz (crítico)

- [ ] `WakeWordEngine` (OpenWakeWord)
- [ ] `FasterWhisperSTT`
- [ ] `KokoroTTS` (+ stub Piper)
- [ ] `OllamaProvider` + `N8nWebhookProvider`
- [ ] `Orchestrator` loop = mismo comportamiento que `jarvis_pro.py`
- [ ] Script `start_jarvis` apunta al nuevo entrypoint

**Criterio:** “Hey Jarvis” → ding → orden → respuesta hablada, offline.

## Fase 2 — Memoria

- [ ] Modelos SQLAlchemy (User, Message, Preference, Note, Project)
- [ ] Short-term (ventana en RAM + DB)
- [ ] Long-term (extractos / preferencias)
- [ ] Prompt de personalidad con nombre del usuario

## Fase 3 — Skills base

- [ ] Registry + skill `open_app`, `open_url`, `search_files`, `calculator`, `timer`
- [ ] Policy de confirmación

## Fase 4 — RAG

- [x] Ingest PDF/DOCX/TXT/MD/CSV/XLSX/PPTX (+ código, JSON, YAML)
- [x] Chroma persistente + indexación incremental
- [x] Skill `ask_docs` + CLI `jarvis index` / `ask` / `watch`
- [x] Citas + refuse si no hay evidencia
- [x] LlamaIndex SentenceSplitter (chunker)

## Fase 5 — Automation

- [x] AutomationEngine + controladores (providers)
- [x] macOS: AppleScript / `open` / Accessibility-lite / papelera
- [x] Browser: system_open + Playwright opcional
- [x] Permisos L1/L2/L3 + auditoría + cancelación por voz
- [x] Skills: open_application, browser, filesystem, clipboard, terminal, screenshot, window_manager
- [x] Integración RAG → URL → navegador
- [x] Windows/Linux: stubs
## Fase 6 — Vision

- [x] VisionProvider / OCRProvider / ScreenProvider / ImageAnalyzer / VisionOrchestrator
- [x] OCR Tesseract + EasyOCR (config)
- [x] Captura full / ventana / región / monitor
- [x] VLM: Ollama / OpenAI / Gemini
- [x] Historial + save_to_knowledge → RAG
- [x] Skills describe/ocr/read/analyze/save + find_on_screen
- [x] Hook visión → automatización (clic por OCR)

## Fase 7 — GUI

- [x] API interna `JarvisGuiController` + protocolo `GuiShell`
- [x] PySide6: estado, chat, config, dashboard
- [x] Bandeja del sistema + notificaciones
- [x] Persistencia de config en `config.yaml`
- [x] `poetry run jarvis gui`
- [x] Placeholders Fase 8

## Fase 8 — Hardening

- [x] ErrorHandler + recuperación TTS/Ollama
- [x] Plugins con manifest + PluginManager + CLI
- [x] Marketplace stub (firma/repo preparados)
- [x] Model Manager (Ollama)
- [x] Secret Manager (Keychain/env)
- [x] Auditoría de seguridad
- [x] Backup / restore
- [x] Autostart macOS/Linux/Windows
- [x] Scripts instalador macOS + .app + stub Windows
- [x] Documentación final de producto

## Fase 9 — Release Candidate

- [x] Versionado semántico (`VERSION`, CHANGELOG, RELEASE_NOTES)
- [x] `jarvis doctor`
- [x] Perfiles performance / balanced / lightweight
- [x] Onboarding CLI + GUI
- [x] Privacidad: export / wipe / mode + comando de voz
- [x] `.app` + `.dmg` (sin firma Apple)
- [x] Checklist Mac limpio + RELEASE_REPORT
- [ ] Validación manual en Mac limpio (operativa)

---

## Orden de implementación inmediata (cuando apruebes)

1. Confirmar `docs/00-PROPUESTAS-ANTES-DE-IMPLEMENTAR.md`
2. Fase 0 archivo por archivo
3. Fase 1 hasta paridad con legacy
4. Recién ahí memoria/skills/RAG

**No** se implementan las 40+ capacidades en paralelo: cada skill es un PR/módulo pequeño.
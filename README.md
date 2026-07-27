# Jarvis — Asistente de voz local-first

Wake word **Hey Jarvis** · Python 3.12+ · Poetry · Clean Architecture

## Estado

| Fase | Estado |
|------|--------|
| 0 — Cimientos | Completa |
| 1 — Voz | Completa |
| 2 — Memoria | Completa |
| 3 — Skills | Completa |
| 4 — RAG / conocimiento | Completa |
| 5 — Automatización OS | Completa |
| 6 — Visión / OCR | Completa |
| 7 — GUI / bandeja | Completa |
| 8 — Producción / hardening | Completa |
| 9 — Release Candidate | **1.0.0-rc.1** |

## Arranque (Fase 1–5)

Requisito: **Python 3.12** (`brew install python@3.12`).

```bash
cd ~/jarvis
./scripts/install.sh
ollama pull llama3.2:3b
ollama pull nomic-embed-text
poetry run jarvis --health
```

### Automatización (Fase 5)

```bash
poetry run jarvis --once-text "Abre Visual Studio Code."
poetry run jarvis --once-text "Copia este texto al portapapeles: hola"
poetry run jarvis --once-text "Abre OpenAI en el navegador."
# Playwright opcional:
# poetry install -E automation && poetry run playwright install chromium
```

Ver: `docs/FASE-5-COMPLETADA.md`, `docs/FASE-6-COMPLETADA.md`, `docs/FASE-7-COMPLETADA.md`.

### Visión (Fase 6)

```bash
brew install tesseract tesseract-lang   # OCR
poetry install -E vision
ollama pull llava
poetry run jarvis --once-text "¿Qué hay en mi pantalla?"
poetry run jarvis --once-text "Guarda esta captura en mi base de conocimiento."
```

### GUI (Fase 7)

```bash
poetry install -E gui
poetry run jarvis gui
```

### Producción (Fase 8)

```bash
./scripts/install_macos.sh
poetry run jarvis plugins list
poetry run jarvis models list
poetry run jarvis backup create
poetry run jarvis autostart install
```

Docs: `docs/INSTALLATION.md`, `docs/USER_GUIDE.md`, `docs/FASE-8-COMPLETADA.md`.

### Release Candidate (Fase 9)

```bash
poetry run jarvis --version    # 1.0.0-rc.1
poetry run jarvis doctor
poetry run jarvis onboard
poetry run jarvis profile apply balanced
poetry run jarvis privacy export
./scripts/create_dmg.sh
```

Docs: `docs/FASE-9-COMPLETADA.md`, `docs/CLEAN_MAC_CHECKLIST.md`, `RELEASE_NOTES.md`.

## Instalación

```bash
cd ~/jarvis
chmod +x scripts/*.sh
./scripts/install.sh
cp .env.example .env   # si aún no existe
poetry run jarvis --health
```

## Comandos

```bash
poetry run jarvis --version
poetry run jarvis --health
poetry run jarvis doctor
poetry run jarvis index [ruta]
poetry run jarvis ask "pregunta"
poetry run jarvis watch [ruta]
poetry run jarvis gui
poetry run jarvis onboard
poetry run jarvis profile list
poetry run jarvis plugins list
poetry run jarvis models list
poetry run jarvis backup create
poetry run jarvis privacy export
poetry run pytest
poetry run pre-commit install
```

## Documentación

- Decisiones: `docs/00-DECISIONES-APROBADAS.md`
- Arquitectura: `docs/01-ARQUITECTURA.md` … `docs/06-DIAGRAMA-MODULOS.md`
- Fase 4: `docs/FASE-4-COMPLETADA.md`
- Fase 5: `docs/FASE-5-COMPLETADA.md`
- Fase 6: `docs/FASE-6-COMPLETADA.md`
- Fase 7: `docs/FASE-7-COMPLETADA.md`
- Fase 8: `docs/FASE-8-COMPLETADA.md`
- Fase 9: `docs/FASE-9-COMPLETADA.md`
- Release: `RELEASE_NOTES.md`, `CHANGELOG.md`, `docs/RELEASE_REPORT.md`
- Instalación: `docs/INSTALLATION.md`
- Usuario: `docs/USER_GUIDE.md`
- Contexto offline: `CONTEXTO-JARVIS.md`

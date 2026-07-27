# Fase 5 completada — Automatización del sistema operativo

**Fecha:** 2026-07-27  
**Estado:** Completa (pendiente de tu OK antes de Fase 6)

## Objetivo

`AutomationEngine` seguro, modular y extensible, con proveedores intercambiables y permisos por niveles.

## Arquitectura

```
Skill → AutomationEngine → PermissionGate + Audit
                         → ApplicationController
                         → BrowserController (system_open | Playwright)
                         → FileController
                         → ClipboardController
                         → WindowController
                         → KeyboardController / MouseController
                         → ShellController
                         → ScreenshotController
```

macOS: implementaciones nativas (`open`, AppleScript, `pbcopy`, `screencapture`, `mdfind`).  
Otras plataformas: stubs hasta ampliar.

## Permisos

| Nivel | Enum | Ejemplos |
|-------|------|----------|
| 1 | SAFE | Abrir apps, URLs, leer archivos, clipboard, screenshot |
| 2 | CONFIRM | Papelera, renombrar, escribir teclado, shell allowlist |
| 3 | RESTRICTED | Borrado permanente, `rm`/`sudo`/diskutil (bloqueado salvo `security.allow_restricted`) |

Cada acción deja descripción + registro en `data/db/automation_audit.db` y logs structlog. Cancelable por voz (`cancela`) en cualquier momento.

## Skills nuevas (auto-descubiertas)

- `open_application`
- `browser` (incluye RAG → URL)
- `filesystem`
- `clipboard`
- `terminal`
- `screenshot`
- `window_manager`

## RAG + automatización

Ejemplo: *«Busca en el manual la URL de staging y ábrela.»*

1. `browser` recupera evidencia vía RAG  
2. Extrae URL  
3. Abre con `BrowserController`

Demo en `knowledge/manual-instalacion.md` (`https://staging.example.com/admin`).

## Config (`automation:` / `security:`)

```yaml
automation:
  enabled: true
  browser_provider: system_open  # o playwright
  audit_db: data/db/automation_audit.db
  shell_allowlist: [ls, pwd, git, ...]
security:
  confirm_destructive: true
  allow_restricted: false
```

Playwright opcional:

```bash
poetry install -E automation
poetry run playwright install chromium
# config: browser_provider: playwright
```

## Capturas de pantalla

Por defecto se guardan en `data/screenshots/` (configurable).

En macOS, la primera vez debes conceder **Grabación de pantalla** a Terminal o Cursor:

Ajustes del Sistema → Privacidad y seguridad → Grabación de pantalla.

## Criterios de aceptación

```bash
poetry run jarvis --once-text "Abre Visual Studio Code."
poetry run jarvis --once-text "Copia este texto al portapapeles: hola"
poetry run jarvis --once-text "Haz una captura de pantalla."
poetry run jarvis --once-text "Abre OpenAI en el navegador."
poetry run jarvis index   # si el manual cambió
poetry run jarvis --once-text "Busca en el manual la URL de staging y ábrela."
```

## Verificación

```bash
poetry run pytest tests/unit/test_automation.py -q
poetry run jarvis --health
```

## Siguiente

Tras tu aprobación → **Fase 6** (visión / OCR / leer pantalla).

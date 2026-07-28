# Jarvis 1.0.0-rc.1 — Release Notes

**Producto:** Jarvis  
**Versión:** 1.0.0-rc.1 (Release Candidate)  
**Fecha:** 2026-07-27  
**Estado:** Candidato a producción — validar en Mac limpio antes de 1.0.0 final.

## Qué es Jarvis

Asistente de voz personal **local-first** para macOS (Windows/Linux en evolución):

- Wake word «Hey Jarvis»
- STT → LLM local (Ollama) → TTS
- Memoria, RAG con citas, skills/plugins
- Automatización OS con permisos
- Visión / OCR (**extra opcional en 1.0.0-rc.1** — ver abajo)
- GUI de escritorio
- Backups, doctor, perfiles de rendimiento

## Cómo instalar (RC)

```bash
cd ~/jarvis
./scripts/install_macos.sh
poetry install -E gui
poetry run jarvis onboard
poetry run jarvis doctor
poetry run jarvis gui
```

Bundle / DMG (desarrollo):

```bash
./scripts/create_app_bundle.sh ~/Applications/Jarvis.app
./scripts/create_dmg.sh
```

## Novedades de este RC

1. Versionado semántico y notas de release.
2. `jarvis doctor` para validar el entorno.
3. Perfiles Performance / Balanced / Lightweight.
4. Onboarding de primera ejecución.
5. Exportar / borrar datos personales y modo privacidad.
6. Scripts de distribución `.app` + `.dmg`.

## Visión / OCR — opt-in (no bloquea 1.0.0)

Para el Release Candidate y la promoción a 1.0.0, **visión no es obligatoria**.

- Sin `llava` ni `tesseract`, `jarvis --health` debe reportar `Vision: degraded` (o `off` si la desactivas en config). Eso es **PASS** del camino base.
- El runtime crítico offline es: Wake → STT → LLM → Memoria → TTS → Skills → RAG → Backup.
- Activar visión después (post-1.0.0 o sesión aparte):

```bash
brew install tesseract tesseract-lang
ollama pull llava
poetry install -E vision   # si usas Poetry
```

Un comando dedicado `jarvis vision install` queda fuera de este RC.

## Offline: runtime vs instalación

- **Runtime** (uso diario): camino crítico local-first — no requiere nube.
- **Instalación**: el DMG es un bootstrap (~cientos de KB); `Install.command` necesita **red** para pip/deps y Ollama para modelos. Offline-first no significa “instalación sin internet”.

## Problemas conocidos

- El `.dmg` no está firmado con Apple Developer ID (Gatekeeper puede pedir «Abrir de todos modos»).
- Instalación vía Poetry o venv standalone + Ollama en el PATH.
- Visión (`llava`) y OCR (Tesseract) son **opcionales**; `doctor`/`--health` advierten si faltan (`Vision: degraded` = OK para 1.0.0 base).
- Kokoro TTS requiere `mlx-audio` en Apple Silicon; fallback a `say` del sistema.

## Criterio para promover a 1.0.0

Completar `docs/CLEAN_MAC_CHECKLIST.md` en un Mac limpio y actualizar `docs/RELEASE_REPORT.md` sin bloqueadores.

## Actualización futura

```bash
./scripts/update.sh
# o: git pull && poetry install && poetry run jarvis doctor
```

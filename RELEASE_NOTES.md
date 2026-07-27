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
- Visión / OCR
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

## Problemas conocidos

- El `.dmg` no está firmado con Apple Developer ID (Gatekeeper puede pedir «Abrir de todos modos»).
- Instalación aún depende de Poetry + Ollama en el PATH (empaquetado standalone completo pendiente de 1.0.0).
- Visión (`llava`) y OCR (Tesseract) son opcionales; `doctor` marca advertencias si faltan.
- Kokoro TTS requiere `mlx-audio` en Apple Silicon; fallback a `say` del sistema.

## Criterio para promover a 1.0.0

Completar `docs/CLEAN_MAC_CHECKLIST.md` en un Mac limpio y actualizar `docs/RELEASE_REPORT.md` sin bloqueadores.

## Actualización futura

```bash
./scripts/update.sh
# o: git pull && poetry install && poetry run jarvis doctor
```

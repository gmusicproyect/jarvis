# Changelog

Todos los cambios notables de Jarvis se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0-rc.1] — 2026-07-27

### Añadido

- Control de versión oficial (`VERSION`, `CHANGELOG.md`, `RELEASE_NOTES.md`).
- `jarvis doctor` — diagnóstico automático (Python, Ollama, audio, DB, Chroma, disco, GPU).
- Perfiles de rendimiento: `performance`, `balanced`, `lightweight` (`jarvis profile`).
- Onboarding guiado (`jarvis onboard`) y flag `app.onboarding_completed`.
- Privacidad: exportar datos, borrar memoria completa, modo privacidad (`jarvis privacy`).
- Instalador macOS: bundle `.app` mejorado + script `create_dmg.sh`.
- Checklist de Mac limpio y `RELEASE_REPORT.md`.
- Comando de voz: «elimina todo lo que recuerdas de mí».

### Cambiado

- Versión de producto: **Jarvis 1.0.0-rc.1** (Release Candidate).
- GUI: pestaña Release (perfiles + doctor resumen) y onboarding en primer arranque.

### Seguridad

- Auditoría de privacidad previa a release.
- Modo privacidad reduce retención de contexto en sesión.

## [0.1.0] — 2026-07-27

### Añadido

- Fases 0–8: voz, memoria, skills, RAG, automatización, visión, GUI, hardening.
- Plugins, Model Manager, backup, autostart, Secret Manager.

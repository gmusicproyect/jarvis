# Fase 8 completada — Hardening, plugins, producción

**Fecha:** 2026-07-27  
**Estado:** Completa (producto listo para uso diario / distribución local)

## Entregado

| Área | Implementación |
|------|----------------|
| Hardening | `ErrorHandler`, `ResilientTTS`, `OllamaHealth` |
| Plugins | `manifest.yaml` + `PluginManager` + marketplace stub |
| Modelos | `ModelManager` (list/pull/remove Ollama) |
| Secretos | Keychain macOS / env / stub Windows |
| Auditoría | `SecurityAudit` |
| Backup | `jarvis backup create\|restore\|list` |
| Autostart | LaunchAgent / systemd / Startup |
| Instaladores | `install_macos.sh`, `create_app_bundle.sh`, stub Windows |
| Docs | INSTALLATION, USER_GUIDE, PLUGINS, SECURITY, ARCHITECTURE_FINAL, TROUBLESHOOTING |

## CLI nueva

```bash
poetry run jarvis plugins list
poetry run jarvis plugins install ./plugins/echo_plugin
poetry run jarvis plugins enable echo_plugin
poetry run jarvis models list
poetry run jarvis models pull llama3.2:3b
poetry run jarvis backup create --label diario
poetry run jarvis backup restore data/backups/….zip
poetry run jarvis autostart install
```

## Criterios

- Instalación en equipo limpio vía scripts + Poetry
- Arranque GUI / voz / autostart
- Memoria y config en backups
- Plugins con permisos validados
- Modelos gestionados por CLI
- Recuperación TTS/Ollama sin tumbar el proceso
- Documentación para otro usuario
- Procedimiento de actualización en `ARCHITECTURE_FINAL.md`

## Verificación

```bash
chmod +x scripts/*.sh
poetry run pytest tests/unit/test_fase8.py -q
poetry run jarvis plugins list
poetry run jarvis backup create --label smoke
poetry run jarvis --health
```

# Arquitectura final Jarvis

```
┌─────────────────────────────────────────────┐
│ GUI (PySide6) / CLI / Voz                   │
│        ↓ GuiShell / comandos                │
│ JarvisGuiController / Orchestrator          │
└─────────────────────────────────────────────┘
          │
┌─────────┴───────────────────────────────────┐
│ Núcleo (providers)                          │
│  Wake · STT · LLM · TTS                     │
│  Memory · RAG · Skills · Plugins            │
│  Automation · Vision · Hardening            │
│  Models · Secrets · Backup · Audit          │
└─────────────────────────────────────────────┘
```

## Capas

| Capa | Paquete |
|------|---------|
| Config | `jarvis.config` |
| Voz | `jarvis.audio`, `jarvis.llm` |
| Memoria | `jarvis.memory` |
| RAG | `jarvis.rag` |
| Skills/Plugins | `jarvis.skills`, `jarvis.plugins` |
| OS | `jarvis.automation` |
| Visión | `jarvis.vision` |
| GUI | `jarvis.gui` |
| Producción | `jarvis.hardening`, `backup`, `security`, `models` |

## Reglas

1. La GUI no contiene lógica de negocio.
2. Todo proveedor es sustituible por config.
3. Fallos de TTS/Ollama no tumban el proceso.
4. Plugins llevan `manifest.yaml` y permisos validados.
5. Backups no incluyen modelos grandes ni cachés.

## Actualización de versiones

1. `jarvis backup create --label pre-update`
2. `git pull` / `./scripts/update.sh`
3. `poetry install -E gui -E vision`
4. `jarvis --health`
5. Si falla → `jarvis backup restore …`

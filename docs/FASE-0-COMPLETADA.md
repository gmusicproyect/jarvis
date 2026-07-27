# Jarvis — Fase 0 completa

## Qué incluye esta fase

- Poetry (`pyproject.toml`) + grupos `dev` / `voice` / `llm` / `rag` / `gui`
- Clean layout en `src/jarvis/`
- `config/config.yaml` + `.env.example`
- Loader tipado (Pydantic)
- Logging estructurado (`structlog`)
- CLI: `jarvis --version` / `jarvis --health`
- Abstracción OS (`platform/`) lista para Fase 5
- Stubs de paquetes para fases futuras (audio, llm, rag, mcp, skills…)
- Scripts `install` / `update` / `start_jarvis`
- Legacy movido a `legacy/` (Hey Jarvis sigue funcionando)
- Pytest + Ruff/Black/pre-commit configurados

## Cómo verificar

```bash
cd ~/jarvis
export PATH="$HOME/.local/bin:$PATH"
poetry run jarvis --health
poetry run pytest
```

## Criterio de salida Fase 0

- [x] Instalable con Poetry
- [x] Config + logging
- [x] Healthcheck OK
- [x] Tests verdes
- [x] Legacy intacto en `legacy/jarvis_pro.py`

## Siguiente (Fase 1) — requiere tu OK

Wake → STT → Ollama → TTS (Kokoro) con providers intercambiables.

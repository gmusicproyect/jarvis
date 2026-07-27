# Árbol del proyecto

```
jarvis/
├── README.md
├── pyproject.toml                 # Poetry
├── poetry.lock
├── .env.example
├── config/
│   ├── config.yaml                # providers, modelos, umbrales
│   └── settings.json              # preferencias de usuario (runtime)
├── docs/
│   ├── 00-PROPUESTAS-ANTES-DE-IMPLEMENTAR.md
│   ├── 01-ARQUITECTURA.md
│   ├── 02-ARBOL.md
│   ├── 03-TECNOLOGIAS-Y-DEPS.md
│   ├── 04-FLUJO.md
│   ├── 05-ROADMAP-Y-FASES.md
│   └── 06-DIAGRAMA-MODULOS.md
├── scripts/
│   ├── install.sh / install.ps1
│   ├── update.sh / update.ps1
│   ├── start_jarvis.sh / start_jarvis.ps1
│   └── start_jarvis.command        # macOS
├── legacy/                        # scripts actuales (migración)
│   ├── jarvis_pro.py
│   ├── jarvis_voz.py
│   ├── jarvis.py
│   └── test_wakeword.py
├── data/
│   ├── db/                        # SQLite
│   ├── chroma/                    # vectores RAG
│   ├── documents/                 # corpus a indexar
│   └── logs/
├── assets/
│   └── sounds/
│       └── activation.wav
├── src/
│   └── jarvis/
│       ├── __init__.py
│       ├── __main__.py            # python -m jarvis
│       ├── app/
│       │   ├── orchestrator.py
│       │   └── lifecycle.py
│       ├── audio/
│       │   ├── wake/
│       │   │   ├── base.py
│       │   │   └── openwakeword_engine.py
│       │   ├── stt/
│       │   │   ├── base.py
│       │   │   └── faster_whisper_stt.py
│       │   └── tts/
│       │       ├── base.py
│       │       ├── kokoro_tts.py
│       │       ├── piper_tts.py
│       │       └── optional_cloud.py   # stubs; disabled by default
│       ├── brain/
│       │   ├── intent.py
│       │   ├── planner.py
│       │   └── conversation.py
│       ├── llm/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── ollama.py
│       │   ├── n8n_webhook.py
│       │   └── optional/          # openai, claude, gemini, mistral…
│       ├── memory/
│       │   ├── short_term.py
│       │   ├── long_term.py
│       │   └── repository.py
│       ├── rag/
│       │   ├── ingest.py
│       │   ├── retrieve.py
│       │   └── store.py
│       ├── skills/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── system/
│       │   ├── browser/
│       │   ├── documents/
│       │   ├── media/
│       │   ├── productivity/
│       │   └── automation/
│       ├── vision/
│       │   ├── ocr.py
│       │   └── screen.py
│       ├── automation/
│       │   ├── base.py
│       │   ├── macos/
│       │   └── windows/
│       ├── database/
│       │   ├── models.py
│       │   ├── session.py
│       │   └── migrations/
│       ├── config/
│       │   ├── loader.py
│       │   └── schema.py
│       ├── prompts/
│       │   └── personality.md
│       ├── api/
│       │   └── server.py          # Fase posterior
│       ├── gui/
│       │   └── tray_app.py
│       ├── security/
│       │   └── policy.py
│       └── utils/
│           ├── logging.py
│           └── metrics.py
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

Los scripts legacy actuales se moverán a `legacy/` en la **Fase 0** sin romper `Jarvis.command` hasta el cutover.
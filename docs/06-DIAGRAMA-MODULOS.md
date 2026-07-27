# Diagrama de módulos

```mermaid
flowchart TB
  subgraph UI["gui/"]
    Tray[TrayApp]
  end

  subgraph APP["app/"]
    Orch[Orchestrator]
    Life[Lifecycle]
  end

  subgraph AUDIO["audio/"]
    Wake[WakeWordEngine]
    STT[STTProvider]
    TTS[TTSProvider]
  end

  subgraph BRAIN["brain/"]
    Intent[IntentClassifier]
    Plan[Planner]
    Conv[Conversation]
  end

  subgraph LLM["llm/"]
    RegLLM[ProviderRegistry]
    Ollama[Ollama]
    N8n[N8nWebhook]
    Cloud[OptionalCloud]
  end

  subgraph MEM["memory/"]
    Short[ShortTerm]
    Long[LongTerm]
    Repo[Repository]
  end

  subgraph RAG["rag/"]
    Ingest[Ingest]
    Retrieve[Retrieve]
    Store[ChromaStore]
  end

  subgraph SK["skills/"]
    RegSk[SkillRegistry]
    Sys[system]
    Br[browser]
    Doc[documents]
    Med[media]
    Prod[productivity]
    Auto[automation]
  end

  subgraph DATA["database/"]
    DB[(SQLite)]
  end

  subgraph CFG["config/"]
    YAML[config.yaml]
    ENV[.env]
  end

  Tray --> Life
  Life --> Orch
  Orch --> Wake
  Orch --> STT
  Orch --> Intent
  Intent --> Plan
  Plan --> RegSk
  Plan --> RegLLM
  Plan --> Retrieve
  RegLLM --> Ollama
  RegLLM --> N8n
  RegLLM --> Cloud
  Orch --> TTS
  Orch --> Short
  Short --> Repo
  Long --> Repo
  Repo --> DB
  Ingest --> Store
  Retrieve --> Store
  CFG --> Orch
  CFG --> RegLLM
  CFG --> Wake
  CFG --> STT
  CFG --> TTS
```

## Dependencias permitidas

- `app` → todos los protocolos
- `skills` → `automation`, `vision`, `rag` (no al revés)
- `llm` → no importa `gui`
- `database` → no importa `audio`

## Mapa brief → módulo

| Capacidad del brief | Módulo |
|---------------------|--------|
| Hey Jarvis | `audio/wake` |
| Whisper | `audio/stt` |
| Voz natural | `audio/tts` |
| GPT/Claude/Ollama… | `llm/` |
| Memoria | `memory/` + `database/` |
| Abrir programas/web | `skills/system`, `skills/browser` |
| PDFs/Office/OCR | `skills/documents`, `vision/` |
| Spotify/YouTube | `skills/media` |
| Mouse/teclado/Windows | `automation/` |
| RAG | `rag/` |
| GUI | `gui/` |
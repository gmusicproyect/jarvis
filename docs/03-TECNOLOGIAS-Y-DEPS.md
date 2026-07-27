# Tecnologías y dependencias

## Stack elegido (MVP local-first)

| Área | Tecnología | Notas |
|------|------------|-------|
| Lenguaje | Python ≥ 3.12 | |
| Deps | Poetry | grupos opcionales |
| Wake word | OpenWakeWord | modelo `hey_jarvis` |
| STT | faster-whisper | default `small`, ES + auto EN |
| TTS | Kokoro (mlx-audio) / Piper | default Kokoro en Apple Silicon |
| LLM | Ollama | modelo configurable |
| Bridge legacy | n8n webhook | opcional |
| DB | SQLite + SQLAlchemy + Alembic | URL → Postgres ready |
| RAG | LlamaIndex + Chroma + Ollama embeddings | |
| GUI | CustomTkinter | tray + panel |
| Tests | pytest + pytest-cov | meta ≥ 80% |
| Logs | logging + RotatingFileHandler | o structlog |
| Audio I/O | sounddevice + numpy | |

## Grupos Poetry (propuestos)

```toml
[tool.poetry.dependencies]
python = "^3.12"
pydantic = "^2"
pydantic-settings = "^2"
pyyaml = "^6"
sqlalchemy = "^2"
alembic = "^1"
httpx = "^0.27"
numpy = "^2"
sounddevice = "^0.5"
faster-whisper = "^1"
openwakeword = "^0.6"
onnxruntime = "^1"

[tool.poetry.group.llm]
optional = true
# ollama via HTTP; SDKs cloud opcionales

[tool.poetry.group.rag]
optional = true
# llama-index, chromadb

[tool.poetry.group.gui]
optional = true
# customtkinter

[tool.poetry.group.dev]
optional = true
# pytest, pytest-cov, ruff, mypy
```

## Proveedores cloud (opcionales, desactivados)

Solo se documentan; **no** son dependencia del camino crítico:

- OpenAI / Anthropic / Google / DeepSeek / Mistral SDKs
- ElevenLabs / Azure Speech / OpenAI TTS

Se instalan con extras Poetry cuando `providers.*.enabled: true`.

## Cambio de proveedor (config)

```yaml
# config/config.yaml (ejemplo)
llm:
  provider: ollama          # ollama | n8n | openai | claude | gemini | mistral | deepseek
  model: llama3.2
  base_url: http://127.0.0.1:11434

stt:
  provider: faster_whisper
  model_size: small         # tiny|base|small|medium|large
  language: es
  auto_detect_english: true

tts:
  provider: kokoro          # kokoro | piper | elevenlabs | azure | openai
  voice: em_santa

wake:
  provider: openwakeword
  phrase: hey_jarvis
  threshold: 0.45
```

Secrets solo en `.env` (`OPENAI_API_KEY`, etc.) — nunca en código.
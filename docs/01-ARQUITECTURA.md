# Arquitectura completa — Jarvis

## Visión

Asistente de voz personal en segundo plano: wake word → STT → intención → LLM/skills → TTS → espera.

Principios:

- **Local-first** (offline por defecto)
- **Providers intercambiables** (LLM / STT / TTS / Wake)
- **Clean Architecture** + SOLID
- **Skills** desacopladas (una capacidad = un módulo)
- **Confirmación humana** en acciones peligrosas

---

## Capas

```
┌─────────────────────────────────────────────────────────┐
│  gui/  (tray, estado mic, start/stop, historial)        │
├─────────────────────────────────────────────────────────┤
│  api/  (opcional: FastAPI local para control remoto)    │
├─────────────────────────────────────────────────────────┤
│  app/  Orchestrator  — loop principal                   │
├──────────────┬──────────────┬───────────────────────────┤
│  audio/      │  brain/      │  skills/                  │
│  wake        │  intent      │  system, browser, docs…   │
│  stt         │  planner     │  vision, automation…      │
│  tts         │  prompts     │                           │
├──────────────┼──────────────┼───────────────────────────┤
│  llm/        │  memory/     │  rag/                     │
│  providers   │  short/long  │  ingest, retrieve         │
├──────────────┴──────────────┴───────────────────────────┤
│  database/  (SQLite → PostgreSQL ready)                 │
│  config/    (.env, config.yaml, settings)               │
│  utils/     (logging, security, metrics)                │
└─────────────────────────────────────────────────────────┘
```

## Contratos (interfaces)

```python
class WakeWordEngine(Protocol):
    def listen_once(self) -> bool: ...

class STTProvider(Protocol):
    def transcribe(self, audio: AudioBuffer) -> Transcript: ...

class TTSProvider(Protocol):
    def speak(self, text: str) -> None: ...

class LLMProvider(Protocol):
    def chat(self, messages: list[Message], tools: list[Tool] | None) -> LLMResponse: ...

class Skill(Protocol):
    name: str
    def can_handle(self, intent: Intent) -> bool: ...
    def run(self, intent: Intent, ctx: Context) -> SkillResult: ...
```

El `Orchestrator` solo habla con protocolos; los providers concretos se inyectan desde `config`.

## Flujo de datos (resumen)

Ver `04-FLUJO.md`.

## Persistencia

- **SQLite** (`database/jarvis.db`): usuarios, preferencias, historial, notas, proyectos.
- Migraciones con **Alembic** (misma capa lista para PostgreSQL vía URL en `.env`).

## Seguridad

- `security/policy.py`: acciones `safe` / `confirm` / `deny`.
- Skills destructivas siempre pasan por `ask_confirmation()` (voz + GUI).

## Observabilidad

- `structlog` o logging std con rotación.
- Métricas: latencia wake→respuesta, tokens (si aplica), RAM/CPU snapshot en GUI.
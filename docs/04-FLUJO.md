# Flujo de funcionamiento

## Loop principal

```
                    ┌──────────────┐
                    │   IDLE       │
                    │ mic abierto  │
                    │ wake listen  │
                    └──────┬───────┘
           "Hey Jarvis"    │
           score > thr     ▼
                    ┌──────────────┐
                    │  ACTIVATED   │
                    │ play ding    │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  LISTENING   │
                    │ VAD / silencio│
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  STT         │
                    │ → texto      │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  BRAIN       │
                    │ intent+plan  │
                    │ memory+RAG   │
                    └──────┬───────┘
                    ┌──────┴───────┐
                    ▼              ▼
             ┌──────────┐   ┌──────────┐
             │  SKILL   │   │   LLM    │
             │ (acción) │   │ (chat)   │
             └────┬─────┘   └────┬─────┘
                  └──────┬───────┘
                         ▼
                    ┌──────────────┐
                    │  TTS speak   │
                    │ (mic pausado)│
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  IDLE        │
                    └──────────────┘
```

## Detalle por paso

1. **Wake** — OpenWakeWord en chunks ~80 ms; bajo CPU.
2. **Ding** — `assets/sounds/activation.wav` (o Ping del sistema).
3. **Listen** — buffer hasta silencio > N s o timeout.
4. **STT** — faster-whisper; idioma `es`, con fallback auto si detecta inglés.
5. **Memory short** — añade turno usuario.
6. **Intent** — clasifica: `chat` | `skill:<name>` | `rag_query` | `dangerous`.
7. **Confirm** — si política = confirm, pregunta por voz/GUI.
8. **Execute** — skill o LLM (con tools + contexto RAG si aplica).
9. **Memory long** — persiste hechos/preferencias relevantes.
10. **TTS** — habla; mic abortado para no auto-escucharse.
11. **Reset wake detector** → IDLE.

## Estados del proceso

| Estado | Mic | Wake | GUI |
|--------|-----|------|-----|
| stopped | off | off | rojo |
| idle | on | on | verde |
| listening | on | off | amarillo |
| thinking | off | off | azul |
| speaking | off | off | morado |
| error | — | — | rojo + log |
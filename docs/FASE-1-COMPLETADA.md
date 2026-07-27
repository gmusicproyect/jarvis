# Fase 1 — Voz completa (implementada)

## Decisiones aplicadas

- Interfaces: `WakeProvider`, `STTProvider`, `LLMProvider`, `TTSProvider`
- Event bus: `wake_detected`, `speech_recognized`, `intent_routed`, `llm_response_ready`, `tts_*`, `followup_*`, `metrics_recorded`
- Métricas: wake/STT/LLM/TTS ms + CPU/RAM (psutil)
- Cancelación: frases en `session.cancel_phrases` (+ monitor durante TTS)
- Follow-up: `session.followup_seconds` tras responder
- Todo parametrizado en `config/config.yaml`

## Flujo

```
Mic → OpenWakeWord → captura → faster-whisper → IntentRouter → Ollama → Kokoro → Altavoz
                                                                              ↓
                                                                    follow-up (N s)
```

## Cómo ejecutar

```bash
# Ollama debe estar corriendo con el modelo de config (llama3.2:3b)
ollama serve   # si no está ya
cd ~/jarvis
poetry run jarvis
```

Prueba parcial sin mic:

```bash
poetry run jarvis --once-text "Hola, ¿estás listo?"
```

## Criterios de aceptación

| Criterio | Estado |
|----------|--------|
| `poetry run jarvis` escucha en fondo | Sí (orchestrator) |
| Detecta Hey Jarvis | Sí (OpenWakeWord + download_models) |
| Sonido activación | Sí (`paths.activation_sound`) |
| STT faster-whisper | Sí |
| Ollama vía provider | Sí (`llama3.2:3b`) |
| Kokoro `em_santa` | Sí (+ fallback `system`) |
| Vuelve a idle / follow-up | Sí |
| Logging estructurado + métricas | Sí |

## Archivos clave

- `src/jarvis/providers/base.py` — protocolos
- `src/jarvis/events/bus.py` — event bus
- `src/jarvis/utils/metrics.py` — latencias
- `src/jarvis/audio/wake/openwakeword_provider.py`
- `src/jarvis/audio/stt/faster_whisper_stt.py`
- `src/jarvis/audio/tts/kokoro_tts.py`
- `src/jarvis/llm/ollama.py`
- `src/jarvis/brain/intent.py`
- `src/jarvis/app/orchestrator.py`
- `src/jarvis/__main__.py`

## Nota deps Kokoro

```bash
poetry run pip install mlx-audio misaki phonemizer-fork espeakng-loader
```

(requerido para español vía EspeakG2P)

## Demo E2E verificada (2026-07-27)

1. `poetry run pytest` → **12 passed**
2. Providers cargan: wake / stt / tts / llm
3. `poetry run jarvis --once-text "..."` → Ollama 200 + **Kokoro reproduce audio**
4. Wake loop: `poetry run jarvis` (requiere micrófono del usuario)

## Cómo probar Hey Jarvis

```bash
# Terminal 1: ollama serve (si no está)
cd ~/jarvis && poetry run jarvis
# Di "Hey Jarvis" (J inglesa) → ding → pregunta → respuesta hablada
# Di "cancela" / "silencio" para cortar TTS
# Tras responder, follow-up ~6s sin repetir Hey Jarvis
```

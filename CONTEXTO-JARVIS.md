# CONTEXTO JARVIS

## Regla de oro

**Todo debe seguir funcionando OFFLINE.**  
Nada de APIs de nube para voz, inteligencia ni STT/TTS en el camino crítico.

| Permitido (local) | Prohibido (nube) |
|---|---|
| Kokoro / mlx-audio | ElevenLabs |
| Piper TTS | OpenAI TTS / Whisper API |
| faster-whisper (local) | Azure / Google Cloud Speech |
| Ollama (local) | ChatGPT / Claude API como cerebro principal |
| n8n en localhost | Servicios SaaS obligatorios |

## Stack actual

- **STT:** faster-whisper (`small`, CPU)
- **Wake word:** openwakeword (`hey_jarvis`)
- **Cerebro:** Ollama + n8n (`http://localhost:5678/webhook/jarvis`)
- **TTS:** Kokoro (`mlx-community/Kokoro-82M-bf16`)
- **Voz por defecto:** `em_alex`  
  Alternativas locales: `em_santa` (masc), `ef_dora` (fem)

## Archivos principales

- `jarvis_pro.py` — Hey Jarvis / aplauso + Kokoro en memoria
- `jarvis_voz.py` — grabación manual + Kokoro
- `jarvis.py` — versión base
- `piper/` — voces Piper (si se usan)
- `venv/` — entorno Python

## Mejoras de voz (solo local)

1. Cambiar `KOKORO_VOZ` a `em_santa` o `ef_dora`
2. Piper con voces `es_ES` / `es_MX`
3. XTTS u otras voces locales entrenadas — nunca nube

## Cómo trabajar con Cursor

Leer este archivo antes de sugerir cambios.  
Si una idea requiere Internet o suscripción, descartarla y proponer alternativa offline.

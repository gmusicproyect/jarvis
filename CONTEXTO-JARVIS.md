# CONTEXTO JARVIS

> **HISTÓRICO / PARCIALMENTE OBSOLETO (2026-07-27)**  
> Este archivo describe el prototipo legacy (`jarvis_pro.py`, `venv/`).  
> El producto activo es `src/jarvis/` (Fases 0–9), Poetry, Python 3.12, versión `1.0.0-rc.1`.  
> Para auditoría y release: `docs/AUDIT_REPORT_rc1.md`, `docs/CLEAN_MAC_CHECKLIST.md`.

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
- **Voz por defecto:** `em_santa`  
  Alternativas locales: `em_alex` (masc), `ef_dora` (fem)

## Archivos principales

- `jarvis_pro.py` — **usar este**: Hey Jarvis / aplauso + Kokoro en memoria
- `jarvis_voz.py` — grabación manual (Enter) — NO tiene wake word
- `jarvis.py` — versión base
- `~/Desktop/Jarvis.command` — atajo que debe lanzar `jarvis_pro.py`
- `venv/` — entorno Python

## Cómo activarlo en el Mac

1. Micrófono: Ajustes → Privacidad → Micrófono → Terminal/Cursor permitidos
2. Doble clic en `Desktop/Jarvis.command` (o `cd ~/jarvis && source venv/bin/activate && python jarvis_pro.py`)
3. Di **"Hey Jarvis"** con J inglesa (como *jungle*), no “yarvis”
4. Espera el *ding*, da la orden, calla ~1.5 s
5. Diagnóstico: `python test_wakeword.py` (mira el score al decir Hey Jarvis)

## Mejoras de voz (solo local)

1. Cambiar `KOKORO_VOZ` a `em_santa` o `ef_dora`
2. Piper con voces `es_ES` / `es_MX`
3. XTTS u otras voces locales entrenadas — nunca nube

## Arquitectura profesional

- **Fase 0–2 completas** — ver `docs/FASE-*-COMPLETADA.md`
- **Python 3.12 LTS** — ver `docs/HOTFIX-PYTHON-312.md`
- Decisiones: `docs/00-DECISIONES-APROBADAS.md`
- LLM: **Ollama directo** · TTS: Kokoro `em_santa` · Memoria: sesión + SQLite + Chroma
- Local-first; cloud opcional vía `config.yaml` / `.env`

## Cómo trabajar con Cursor

Leer este archivo y `docs/00-DECISIONES-APROBADAS.md` antes de sugerir cambios.  
No avanzar de fase sin aprobación del usuario.  
Camino crítico offline por defecto.  
Usar Python **3.12** (`poetry env use python3.12`).

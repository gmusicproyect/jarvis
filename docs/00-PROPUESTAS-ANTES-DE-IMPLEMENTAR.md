# Propuestas antes de implementar

Este documento marca **conflictos** entre el brief de arquitectura y el Jarvis que ya tienes en `~/jarvis`.  
**No se implementa código de la nueva arquitectura hasta que confirmes estas decisiones.**

---

## 1. Sistema operativo: Windows 11 vs macOS (actual)

| Brief | Realidad |
|-------|----------|
| Windows 11 | Tu Mac + scripts `.command` + Kokoro MLX (Apple Silicon) |

**Propuesta:** arquitectura **cross-platform**.

- Núcleo (`brain`, `llm`, `memory`, `audio` abstracto) = multiplataforma.
- Capa `automation/` con adaptadores:
  - `automation/macos/` (AppleScript, `open`, Accessibility)
  - `automation/windows/` (pywinauto, PowerShell, Win32)
- Por defecto en este repo: **macOS first** (porque es tu máquina hoy).
- Windows se añade en Fase 5 sin reescribir el núcleo.

**Ventaja:** no tiras el trabajo actual ni dependes de un PC que aún no usas como host principal.

---

## 2. Regla OFFLINE vs proveedores en la nube

Tu `CONTEXTO-JARVIS.md` prohíbe ElevenLabs / OpenAI TTS / APIs como cerebro crítico.  
El brief pide OpenAI, Claude, Gemini, ElevenLabs, Azure…

**Propuesta:** patrón **Provider + Local-first**.

- Camino por defecto (sin `.env` de nube):  
  **Ollama + OpenWakeWord + faster-whisper + Kokoro/Piper**
- Proveedores cloud = **opcionales**, activados solo si `providers.*.enabled: true` en `config.yaml`.
- El núcleo nunca importa SDKs de nube en el hot path si el provider es `local`.

**Ventaja:** cumples el brief de “cambiar proveedor en config” **y** conservas Jarvis privado offline.

---

## 3. Poetry + venv existente

Hoy usas `venv/`. El brief pide Poetry.

**Propuesta:** migrar a **Poetry** en la nueva estructura `src/jarvis/`, dejando los scripts legacy (`jarvis_pro.py`, etc.) en `/legacy` hasta Fase 2.

**Ventaja:** deps reproducibles, grupos `dev` / `voice` / `rag` / `gui` para no instalar todo de golpe.

---

## 4. Cerebro: n8n vs LLM directo

Hoy: webhook n8n → Ollama.  
Brief: LLM adapters directos.

**Propuesta:** interfaz `LLMProvider` con implementaciones:

1. `OllamaProvider` (default)
2. `N8nWebhookProvider` (compatibilidad con tu flujo actual)
3. `OpenAIProvider` / `ClaudeProvider` / … (opcionales)

**Ventaja:** no rompes n8n el día 1; puedes migrar a LLM directo cuando quieras.

---

## 5. TTS: ElevenLabs vs Kokoro

**Propuesta default:** Kokoro (macOS/MLX) + Piper (cross-platform offline).  
ElevenLabs / Azure / OpenAI TTS = plugins opcionales detrás de `TTSProvider`.

Voz “mayordomo”: `em_santa` (Kokoro) o Piper `es_ES` male — entrenar/ajustar tono en prompts, no en la nube.

---

## 6. RAG: no uses LangChain + LlamaIndex + FAISS + Chroma a la vez

**Propuesta:**

| Pieza | Elección |
|-------|----------|
| Orquestación docs | **LlamaIndex** (más limpio para indexar carpetas) |
| Vector store | **ChromaDB** (persistente, simple) |
| Embeddings | `nomic-embed-text` vía Ollama (offline) |

LangChain y FAISS = fuera del MVP (se pueden añadir después si hace falta).

**Ventaja:** menos superficie, menos bugs, mismo resultado.

---

## 7. GUI

**Propuesta:** **CustomTkinter** + icono en menubar/tray (ligero, Python puro).  
Evitar Electron/Tauri en MVP.

---

## 8. Monolito legacy vs paquete nuevo

**Propuesta:**

```
~/jarvis/
  legacy/          # jarvis_pro.py, jarvis_voz.py, test_wakeword.py (siguen funcionando)
  src/jarvis/      # arquitectura limpia nueva
  docs/            # esta arquitectura
```

Hasta que `python -m jarvis` esté estable, `Jarvis.command` puede apuntar a legacy.

---

## Decisiones que necesito de ti

Responde con sí/no o la opción:

1. **OS:** ¿Cross-platform con prioridad macOS, o solo Windows 11?
2. **Offline:** ¿Local-first con cloud opcional, o cloud permitido en el camino crítico?
3. **Cerebro:** ¿Mantener n8n en Fase 1, o ir directo a Ollama?
4. **TTS default:** ¿Kokoro (`em_santa`) o Piper?
5. **Empezar implementación:** ¿Fase 0 (esqueleto Poetry + config + loop wake) ya?

Cuando confirmes, implementamos **archivo por archivo** según el plan de fases.
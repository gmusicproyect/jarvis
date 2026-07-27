# Fase 6 completada — Visión, OCR y comprensión de pantalla

**Fecha:** 2026-07-27  
**Estado:** Completa (pendiente de tu OK antes de Fase 7)

## Objetivo

Jarvis puede capturar la pantalla, extraer texto (OCR) y analizar imágenes con un modelo de visión configurable; puede indexar el resultado en RAG y preparar clics por OCR.

## Arquitectura

```
ScreenProvider → captura
OCRProvider    → Tesseract | EasyOCR | stub
VisionProvider → Ollama | OpenAI | Gemini | stub
ImageAnalyzer  → OCR + VLM
VisionOrchestrator → skills + historial + knowledge
```

## Config (`vision:`)

```yaml
vision:
  enabled: true
  provider: ollama          # ollama | openai | gemini | stub
  model: llava
  ocr_provider: tesseract   # tesseract | easyocr | stub
  ocr_languages: [spa, eng]
  captures_dir: data/screenshots
  history_db: data/db/vision_history.db
```

### Dependencias opcionales

```bash
# OCR Tesseract
brew install tesseract tesseract-lang
poetry install -E vision

# EasyOCR (más pesado)
poetry install -E vision-easyocr

# Modelo local de visión
ollama pull llava
# o: ollama pull qwen2.5vl
```

OpenAI / Gemini usan `OPENAI_API_KEY` / `GOOGLE_API_KEY` del entorno.

## Skills

| Skill | Uso |
|-------|-----|
| `describe_screen` | ¿Qué hay en mi pantalla? |
| `read_screen` | Lee la pantalla |
| `ocr_image` | Lee el texto / OCR |
| `analyze_image` | Analiza imagen por ruta |
| `save_to_knowledge` | Guarda captura → `knowledge/` + índice RAG |
| `find_on_screen` | Busca botón; clic con confirmación |

## Captura

- Pantalla completa
- Ventana activa
- Región `(x,y,w,h)`
- Monitor específico (`-D N` en macOS)

## Historial

Tabla `vision_history` en `data/db/vision_history.db`: fecha, imagen, OCR, resumen, etiquetas, modelo, tiempos.

## Integración

- **RAG:** `save_to_knowledge` escribe Markdown e indexa.
- **Automatización:** `find_on_screen` + `PermissionLevel.CONFIRM` para clic en coordenadas OCR.

## Criterios de aceptación

```bash
poetry run jarvis --once-text "¿Qué hay en mi pantalla?"
poetry run jarvis --once-text "Lee el texto de esta imagen."
poetry run jarvis --once-text "Guarda esta captura en mi base de conocimiento."
poetry run jarvis --once-text "Busca el botón Continuar."
```

## Verificación

```bash
poetry run pytest tests/unit/test_vision.py -q
poetry run jarvis --health   # Vision: on (...)
```

## Nota macOS

Concede **Grabación de pantalla** a Terminal/Cursor en Ajustes del Sistema.

## Siguiente

Tras tu aprobación → **Fase 7** (GUI / bandeja / panel de estado).

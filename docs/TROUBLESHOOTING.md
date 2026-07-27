# Solución de problemas

## Ollama no responde

```bash
ollama serve
ollama list
poetry run jarvis models list
```

Jarvis sigue ofreciendo skills locales mientras reintenta.

## TTS no habla

Kokoro falla → fallback automático a `say` (macOS).  
Revisa `ESPEAK_DATA_PATH` y `poetry run pip install mlx-audio misaki …` (ver `docs/HOTFIX-PYTHON-312.md`).

## Wake word no detecta

Baja `wake.threshold` en config (p.ej. 0.35).  
Comprueba permiso de micrófono.

## Captura / OCR falla

Concede **Grabación de pantalla**.  
`brew install tesseract tesseract-lang` y `poetry install -E vision`.

## GUI no abre

```bash
poetry install -E gui
poetry run jarvis gui
```

## Plugins no cargan

```bash
poetry run jarvis plugins list
# debe existir plugins/<nombre>/manifest.yaml
```

## Restaurar datos

```bash
poetry run jarvis backup list
poetry run jarvis backup restore data/backups/….zip
```

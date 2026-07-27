# Fase 7 completada — GUI, bandeja y panel de estado

**Fecha:** 2026-07-27  
**Estado:** Completa (pendiente de tu OK antes de Fase 8)

## Objetivo

Aplicación de escritorio completa: la GUI **no** contiene lógica de negocio; solo consume `JarvisGuiController`.

## Arquitectura

```
gui/
  api/          ← controlador + modelos + protocolo GuiShell
  qt/           ← PySide6 (ventana, tray, estilos)
```

Contrato `GuiShell` preparado para sustituir Qt por web/Tauri sin tocar el núcleo.

## Componentes

| Pieza | Contenido |
|-------|-----------|
| Estado | Wake, LLM, visión, OCR, RAG, memoria, Ollama, mic, TTS, CPU/RAM, latencia |
| Conversación | Texto usuario/Jarvis, tiempo, skills, fuentes RAG |
| Configuración | Persistencia automática en `config.yaml` |
| Dashboard | Memoria, docs indexados, skills, automatizaciones, visión, auditoría |
| Bandeja | Iniciar/detener, mic, ventana, config, logs, salir |
| Notificaciones | Tray nativas (info/warning/error) |
| Próximamente | Placeholders Fase 8 (plugins, marketplace, agentes…) |

## Arranque

```bash
poetry install -E gui
# o: poetry install --with gui

poetry run jarvis gui
```

## Criterios de aceptación

- Iniciar/detener Jarvis desde la UI o la bandeja
- Ver estado de módulos en tiempo real (refresh 2s)
- Cambiar modelo/voz/RAG y guardar → `config.yaml`
- Chat por texto en la consola
- Dashboard con historiales
- Notificaciones del sistema
- Control total desde la bandeja

## Verificación

```bash
poetry run pytest tests/unit/test_gui.py -q
poetry run jarvis --health   # GUI: on (qt)
poetry run jarvis gui
```

## Siguiente

Tras tu aprobación → **Fase 8** (hardening, plugins, installers, cutover).

# Instalación de Jarvis

## Requisitos

- macOS 13+ (prioritario) o Linux/Windows
- Python 3.12
- Poetry
- Ollama (`ollama serve`)

## Instalación rápida (macOS)

```bash
cd ~/jarvis
chmod +x scripts/*.sh
./scripts/install_macos.sh
# opcional autostart:
./scripts/install_macos.sh --autostart

# App bundle
./scripts/create_app_bundle.sh
open ~/Applications/Jarvis.app
```

## Permisos macOS

En **Ajustes del Sistema → Privacidad y seguridad** concede a Terminal/Cursor/Jarvis:

| Permiso | Para qué |
|---------|----------|
| Micrófono | Wake word + STT |
| Grabación de pantalla | Visión / OCR |
| Accesibilidad | Automatización UI |
| Notificaciones | Recordatorios / errores |

## Arranque diario

```bash
poetry run jarvis gui          # interfaz + bandeja
poetry run jarvis              # solo voz (terminal)
poetry run jarvis autostart install
```

## Windows (base)

Ver `scripts/install_windows.ps1.stub` y empaquetado PyInstaller + NSIS/WiX.

## Actualización

```bash
./scripts/update.sh
poetry run jarvis backup create --label pre-update
```

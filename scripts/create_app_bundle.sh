#!/usr/bin/env bash
# Crea un .app que lanza Jarvis GUI sin exigir `poetry` en el PATH.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="${1:-$HOME/Applications/Jarvis.app}"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RES="$CONTENTS/Resources"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
ICON_SRC="$ROOT/assets/icons/Jarvis.icns"

mkdir -p "$MACOS" "$RES"

if [[ -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$RES/Jarvis.icns"
  ICON_KEY=$'\n  <key>CFBundleIconFile</key><string>Jarvis</string>'
else
  ICON_KEY=""
fi

cat > "$CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Jarvis</string>
  <key>CFBundleDisplayName</key><string>Jarvis</string>
  <key>CFBundleIdentifier</key><string>com.jarvis.assistant</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>Jarvis</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>${ICON_KEY}
  <key>NSHighResolutionCapable</key><true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>Jarvis necesita el micrófono para escucharte con Hey Jarvis.</string>
  <key>NSAppleEventsUsageDescription</key>
  <string>Jarvis usa AppleEvents para automatizar aplicaciones.</string>
  <key>NSScreenCaptureUsageDescription</key>
  <string>Jarvis captura la pantalla para visión y OCR cuando lo pides.</string>
</dict>
</plist>
EOF

cp "$ROOT/scripts/resolve_python.sh" "$RES/resolve_python.sh"
chmod +x "$RES/resolve_python.sh"

PIN_PY=""
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

_is_portable_python() {
  case "$1" in
    */cursor-sandbox-cache/*|*/TemporaryItems/*|/var/folders/*)
      return 1
      ;;
  esac
  return 0
}

if [[ -x "$ROOT/.runtime/venv/bin/python" ]]; then
  PIN_PY="$ROOT/.runtime/venv/bin/python"
elif command -v poetry >/dev/null 2>&1; then
  ENV_P="$(cd "$ROOT" && poetry env info -p 2>/dev/null || true)"
  if [[ -n "$ENV_P" && -x "$ENV_P/bin/python" ]] && _is_portable_python "$ENV_P/bin/python"; then
    PIN_PY="$ENV_P/bin/python"
  fi
fi
if [[ -n "$PIN_PY" ]]; then
  printf '%s\n' "$PIN_PY" > "$RES/python.path"
  if mkdir -p "$ROOT/.runtime" 2>/dev/null; then
    printf '%s\n' "$PIN_PY" > "$ROOT/.runtime/python.path"
  fi
  # Siempre pin en Application Support (sobrevive al desmontar el DMG)
  mkdir -p "${HOME}/Library/Application Support/Jarvis"
  printf '%s\n' "$PIN_PY" > "${HOME}/Library/Application Support/Jarvis/python.path"
  echo "Python fijado: $PIN_PY"
else
  echo "AVISO: sin python.path portable. En Mac limpio ejecuta ./scripts/install_standalone_macos.sh"
  rm -f "$RES/python.path"
fi

cat > "$MACOS/Jarvis" <<EOF
#!/bin/zsh
set -euo pipefail
export PATH="\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
export JARVIS_ROOT="$ROOT"
RES="\$(cd "\$(dirname "\$0")/../Resources" && pwd)"
cd "\$JARVIS_ROOT"

PY=""
if [[ -f "\$RES/python.path" ]]; then
  PY="\$(tr -d '[:space:]' < "\$RES/python.path")"
fi

if [[ -z "\$PY" || ! -x "\$PY" ]]; then
  resolve="\$RES/resolve_python.sh"
  [[ -x "\$resolve" ]] || resolve="\$JARVIS_ROOT/scripts/resolve_python.sh"
  if ! PY="\$("\$resolve")"; then
    osascript -e 'display dialog "Jarvis no encuentra Python. Ejecuta ./scripts/install_standalone_macos.sh" buttons {"OK"} default button 1'
    exit 1
  fi
fi

export PYTHONPATH="\$JARVIS_ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
if ! "\$PY" -c "import jarvis" 2>/dev/null; then
  osascript -e 'display dialog "Jarvis no está instalado en este Python. Ejecuta ./scripts/install_standalone_macos.sh" buttons {"OK"} default button 1'
  exit 1
fi

exec "\$PY" -m jarvis gui
EOF
chmod +x "$MACOS/Jarvis"

cat > "$RES/Permissions.rtf" <<'EOF'
{\rtf1\ansi\deff0
{\fonttbl{\f0 Helvetica;}}
\f0\fs24 Jarvis — permisos macOS\par
\par
1. Micrófono\par
2. Grabación de pantalla / Screen Recording\par
3. Accesibilidad\par
4. Notificaciones\par
\par
Ajustes del Sistema → Privacidad y seguridad.\par
}
EOF

echo "App bundle creado en: $APP_DIR (v${VERSION})"
echo "Launcher: python.path / resolve_python → python -m jarvis gui (sin Poetry)"
echo "Abre con: open \"$APP_DIR\""
echo "Para DMG: ./scripts/create_dmg.sh"

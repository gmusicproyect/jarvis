#!/usr/bin/env bash
# Empaqueta Jarvis.app en un .dmg distribuible (sin firma Apple por defecto).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
DIST="$ROOT/dist"
STAGE="$DIST/dmg-stage"
APP_NAME="Jarvis.app"
DMG_NAME="Jarvis-${VERSION}.dmg"
VOL_NAME="Jarvis ${VERSION}"

mkdir -p "$DIST"
rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "==> Creando app bundle…"
"$ROOT/scripts/create_app_bundle.sh" "$STAGE/$APP_NAME"

# Enlace a /Applications para drag-and-drop
ln -sf /Applications "$STAGE/Applications"

# Incluir el código + scripts para instalación standalone en Mac limpio
echo "==> Copiando runtime del proyecto al DMG (sin .venv/data pesados)…"
rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '.runtime' \
  --exclude 'dist' \
  --exclude 'data/backups' \
  --exclude 'data/chroma' \
  --exclude 'data/chroma_rag' \
  --exclude 'data/exports' \
  --exclude 'data/screenshots' \
  --exclude 'data/logs' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'poetry.lock' \
  "$ROOT/" "$STAGE/JarvisSource/"

# Apuntar el .app del DMG al código incluido en el volumen
"$ROOT/scripts/create_app_bundle.sh" "$STAGE/$APP_NAME" 2>/dev/null || true
# Reescribir launcher ROOT al source del DMG (ruta relativa vía volumen)
# El usuario debe ejecutar Install.command tras montar

cat > "$STAGE/Install.command" <<'EOF'
#!/bin/zsh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/JarvisSource"
chmod +x scripts/*.sh
./scripts/install_standalone_macos.sh
open "$HOME/Applications/Jarvis.app"
EOF
chmod +x "$STAGE/Install.command"

# README de primera ejecución
cat > "$STAGE/LEEME.txt" <<EOF
Jarvis ${VERSION}
=================

INSTALACIÓN EN MAC LIMPIO (sin Poetry):

1. Doble clic en Install.command  (o arrastra JarvisSource y ejecuta
   ./scripts/install_standalone_macos.sh).
2. Se crea ~/Applications/Jarvis.app con venv propio.
3. Concede permisos: Micrófono, Pantalla, Accesibilidad, Notificaciones.
4. Instala Ollama: https://ollama.com
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text
5. Primera vez: onboarding automático al abrir la GUI
   o: ~/Library/Application\\ Support/Jarvis/venv/bin/jarvis onboard
6. Diagnóstico: .../venv/bin/jarvis doctor

Gatekeeper (RC sin firma):
  clic derecho → Abrir en Jarvis.app / Install.command

Firma/notarización (1.0.0):
  ./scripts/codesign_and_notarize.sh
EOF

echo "==> Creando DMG…"
rm -f "$DIST/$DMG_NAME"
hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$STAGE" \
  -ov -format UDZO \
  "$DIST/$DMG_NAME"

rm -rf "$STAGE"
echo "DMG listo: $DIST/$DMG_NAME"
echo "Montar: open \"$DIST/$DMG_NAME\""

# Firma opcional si hay identidad
if [[ "${JARVIS_CODESIGN_ID:-}" != "" ]]; then
  echo "==> Firmando con $JARVIS_CODESIGN_ID…"
  codesign --force --deep --sign "$JARVIS_CODESIGN_ID" "$DIST/$DMG_NAME" || true
fi

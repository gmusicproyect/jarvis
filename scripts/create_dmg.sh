#!/usr/bin/env bash
# Empaqueta Jarvis en un .dmg distribuible (sin firma Apple por defecto).
#
# P1-A: NO incluir Jarvis.app ni symlink a /Applications en el volumen.
# Ese .app se horneaba con JARVIS_ROOT/python.path de la máquina de build
# y rompía a quien arrastrara la app. El único camino soportado es
# Install.command → Application Support + ~/Applications/Jarvis.app fresco.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
DIST="$ROOT/dist"
STAGE="$DIST/dmg-stage"
DMG_NAME="Jarvis-${VERSION}.dmg"
VOL_NAME="Jarvis ${VERSION}"

mkdir -p "$DIST"
rm -rf "$STAGE"
mkdir -p "$STAGE"

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

cat > "$STAGE/Install.command" <<'EOF'
#!/bin/zsh
set -euo pipefail
# Único camino soportado: Install.command (no arrastrar .app).
# El DMG es de solo lectura: install_standalone copia a
# ~/Library/Application Support/Jarvis y crea el venv ahí.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/JarvisSource"
chmod +x scripts/*.sh
./scripts/install_standalone_macos.sh
open "$HOME/Applications/Jarvis.app"
EOF
chmod +x "$STAGE/Install.command"

cat > "$STAGE/LEEME.txt" <<EOF
Jarvis ${VERSION}
=================

INSTALACIÓN (único camino soportado):

1. Doble clic en Install.command
   — NO busques un Jarvis.app dentro del DMG para arrastrarlo a
     Applications: ese atajo no está incluido a propósito (rompía
     instalaciones con rutas de la máquina de build).
2. Install.command copia el código a
   ~/Library/Application Support/Jarvis/repo
   crea el venv en …/Jarvis/venv
   y genera ~/Applications/Jarvis.app + ~/.local/bin/jarvis
3. Concede permisos: Micrófono, Pantalla, Accesibilidad, Notificaciones.
4. Instala Ollama: https://ollama.com
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text
5. Primera vez: onboarding al abrir la GUI, o: jarvis onboard
6. Diagnóstico: jarvis doctor

Gatekeeper (RC sin firma):
  clic derecho → Abrir en Install.command

Firma/notarización (1.0.0):
  ./scripts/codesign_and_notarize.sh
EOF

echo "==> Creando DMG (solo JarvisSource + Install.command + LEEME)…"
rm -f "$DIST/$DMG_NAME"
hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$STAGE" \
  -ov -format UDZO \
  "$DIST/$DMG_NAME"

rm -rf "$STAGE"
echo "DMG listo: $DIST/$DMG_NAME"
echo "Montar: open \"$DIST/$DMG_NAME\""

if [[ "${JARVIS_CODESIGN_ID:-}" != "" ]]; then
  echo "==> Firmando con $JARVIS_CODESIGN_ID…"
  codesign --force --deep --sign "$JARVIS_CODESIGN_ID" "$DIST/$DMG_NAME" || true
fi

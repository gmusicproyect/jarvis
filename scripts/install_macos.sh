#!/usr/bin/env bash
# Instalación macOS de Jarvis (app local + permisos guía)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Jarvis — instalación macOS"
"$ROOT/scripts/install.sh"

echo ""
echo "==> Permisos de macOS (conceder manualmente en Ajustes del Sistema):"
echo "  • Micrófono          → Terminal / Cursor / Jarvis"
echo "  • Grabación pantalla → Terminal / Cursor / Jarvis"
echo "  • Accesibilidad      → Terminal / Cursor / Jarvis (automatización)"
echo "  • Notificaciones     → Jarvis (GUI)"
echo ""

if [[ "${1:-}" == "--autostart" ]]; then
  poetry run jarvis autostart install
  echo "Autostart (LaunchAgent) instalado."
fi

echo "Listo. Arranque:"
echo "  poetry run jarvis gui"
echo "  o: ./scripts/start_jarvis.sh gui"

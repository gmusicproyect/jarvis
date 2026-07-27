#!/usr/bin/env bash
# Firma y notarización Apple (requiere Developer ID).
# Uso:
#   export JARVIS_CODESIGN_ID="Developer ID Application: Tu Nombre (TEAMID)"
#   export JARVIS_NOTARY_PROFILE="jarvis-notary"   # xcrun notarytool store-credentials
#   ./scripts/codesign_and_notarize.sh [ruta.app] [ruta.dmg]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
APP="${1:-$HOME/Applications/Jarvis.app}"
DMG="${2:-$ROOT/dist/Jarvis-${VERSION}.dmg}"

if [[ -z "${JARVIS_CODESIGN_ID:-}" ]]; then
  cat <<EOF
Falta JARVIS_CODESIGN_ID.

Ejemplo:
  export JARVIS_CODESIGN_ID="Developer ID Application: Juan Lizama (XXXXXXXX)"
  # Una vez:
  xcrun notarytool store-credentials jarvis-notary \\
    --apple-id "tu@email.com" --team-id "TEAMID" --password "app-specific-password"
  export JARVIS_NOTARY_PROFILE="jarvis-notary"
  ./scripts/codesign_and_notarize.sh
EOF
  exit 1
fi

if [[ ! -d "$APP" ]]; then
  echo "No existe $APP — genera con ./scripts/create_app_bundle.sh"
  exit 1
fi

echo "==> Firmando app: $APP"
codesign --force --deep --options runtime --sign "$JARVIS_CODESIGN_ID" "$APP"
codesign --verify --deep --strict "$APP"
echo "Firma app OK"

if [[ -f "$DMG" ]]; then
  echo "==> Firmando DMG: $DMG"
  codesign --force --sign "$JARVIS_CODESIGN_ID" "$DMG" || true
fi

if [[ -n "${JARVIS_NOTARY_PROFILE:-}" && -f "$DMG" ]]; then
  echo "==> Enviando a notarización Apple…"
  xcrun notarytool submit "$DMG" --keychain-profile "$JARVIS_NOTARY_PROFILE" --wait
  echo "==> Grapando ticket…"
  xcrun stapler staple "$DMG"
  xcrun stapler validate "$DMG"
  echo "Notarización OK — Gatekeeper no debería advertir."
else
  echo "Omitida notarización (define JARVIS_NOTARY_PROFILE y genera el DMG)."
fi

echo "Listo."

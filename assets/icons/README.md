# Iconos

Coloca aquí `Jarvis.icns` para que `scripts/create_app_bundle.sh` lo incruste en el `.app`.

Generación rápida (opcional):

```bash
# Desde un PNG 1024x1024:
mkdir -p Jarvis.iconset
sips -z 16 16     icon.png --out Jarvis.iconset/icon_16x16.png
sips -z 32 32     icon.png --out Jarvis.iconset/diana_32x32.png
# … o usa iconutil tras poblar el iconset
iconutil -c icns Jarvis.iconset -o assets/icons/Jarvis.icns
```

Sin `.icns`, el bundle usa el icono genérico de macOS.

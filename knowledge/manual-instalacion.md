# Manual de instalación de Jarvis

## Requisitos

- Python 3.12
- Poetry
- Ollama con los modelos `llama3.2:3b` y `nomic-embed-text`

## Instalación

1. Clona el repositorio en `~/jarvis`.
2. Ejecuta `./scripts/install.sh`.
3. Copia `.env.example` a `.env`.
4. Arranca Ollama.
5. Ejecuta `poetry run jarvis --health`.

## Vacaciones (ejemplo contractual)

Los empleados tienen derecho a **15 días hábiles** de vacaciones al año.
Las vacaciones deben solicitarse con **10 días de anticipación**.
No se pueden acumular más de **5 días** para el año siguiente.

## Kubernetes

El despliegue de demostración usa un Deployment llamado `jarvis-api`
en el namespace `jarvis`. La imagen se publica en el registry interno.

## URLs de entorno

- Staging: https://staging.example.com/admin
- Producción: https://prod.example.com/admin
- Panel de administración del servidor de producción: https://prod.example.com/admin

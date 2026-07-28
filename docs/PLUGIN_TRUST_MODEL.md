# Modelo de confianza — Plugins

El sistema de plugins admite únicamente plugins desarrollados y distribuidos
por el proyecto (o por el operador del sistema). Los plugins se consideran
código de confianza y se ejecutan con los mismos privilegios que la aplicación
mediante exec_module.

No existe aislamiento, firma criptográfica ni permisos en tiempo de ejecución.
La instalación de plugins de terceros no está soportada.

## Nota de futuro

Si en una versión posterior se admite la instalación de plugins de terceros,
será necesario rediseñar el subsistema para incorporar al menos:

1. Validación de compatibilidad del manifiesto
2. Autenticidad (firma o lista de confianza)
3. Aislamiento (proceso separado o sandbox, según la plataforma)
4. Gestión de dependencias y permisos

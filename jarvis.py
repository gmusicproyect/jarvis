#!/usr/bin/env python3
"""JARVIS LOCAL - Habla con tu IA local a traves de n8n + Ollama."""

import subprocess
import sys

import requests

WEBHOOK_URL = "http://localhost:5678/webhook/jarvis"
VOZ = "Monica"  # voz en espanol de macOS; cambiala con: say -v ? | grep es_


def hablar(texto):
    """Jarvis habla usando la voz nativa de macOS."""
    subprocess.run(["say", "-v", VOZ, texto], check=False)


def preguntar(mensaje):
    """Envia el mensaje al workflow de n8n y devuelve la respuesta."""
    try:
        r = requests.post(WEBHOOK_URL, json={"mensaje": mensaje}, timeout=180)
        r.raise_for_status()
        return r.json().get("respuesta", "(Jarvis no dijo nada)")
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        return f"(error: {e})"


def main():
    print("JARVIS LOCAL - escribe 'salir' para terminar")
    hablar("Jarvis en linea")
    while True:
        try:
            mensaje = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not mensaje:
            continue
        if mensaje.lower() in ("salir", "exit", "quit"):
            hablar("Hasta luego, Juan")
            break
        print("Jarvis esta pensando...")
        respuesta = preguntar(mensaje)
        if respuesta is None:
            print("No puedo conectar con n8n. Esta corriendo en http://localhost:5678 ?")
            continue
        print(f"Jarvis: {respuesta}")
        hablar(respuesta)


if __name__ == "__main__":
    sys.exit(main())

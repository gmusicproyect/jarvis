#!/usr/bin/env python3
"""JARVIS VOZ - Le hablas, Jarvis escucha (Whisper), piensa (Ollama+n8n) y responde (Kokoro TTS)."""

import glob
import os
import subprocess
import sys
import termios
import time

import numpy as np
import requests
import sounddevice as sd

WEBHOOK_URL = "http://localhost:5678/webhook/jarvis"
KOKORO_MODEL = "mlx-community/Kokoro-82M-bf16"
KOKORO_VOZ = "em_alex"      # masculina espanol; alternativas: em_santa (masc), ef_dora (fem)
MODELO_WHISPER = "small"
SAMPLE_RATE = 16000

print("Cargando oidos de Jarvis...")
from faster_whisper import WhisperModel
modelo = WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")


def hablar(texto):
    """Jarvis habla con Kokoro TTS (voz neuronal en espanol, Apple Silicon)."""
    try:
        base = "/tmp/jarvis_kokoro"
        for viejo in glob.glob(base + "_*.wav"):
            os.remove(viejo)
        texto_split = texto.replace(". ", ".\n")  # ayuda al G2P en espanol
        subprocess.run(
            [sys.executable, "-m", "mlx_audio.tts.generate",
             "--model", KOKORO_MODEL, "--text", texto_split,
             "--voice", KOKORO_VOZ, "--lang_code", "e",
             "--file_prefix", base],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wavs = sorted(glob.glob(base + "_*.wav"))
        if not wavs:
            raise RuntimeError("Kokoro no genero audio")
        for wav in wavs:
            subprocess.run(["afplay", wav], check=False)
    except Exception as e:
        print("Kokoro fallo, usando voz del sistema:", repr(e))
        subprocess.run(["say", texto], check=False)


def grabar():
    """Graba tu voz hasta que presiones Enter."""
    print("Grabando... habla y presiona Enter al terminar")
    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="float32", callback=callback):
        time.sleep(0.3)
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
        input()
    if not frames:
        return np.array([], dtype="float32")
    return np.concatenate(frames, axis=0).squeeze()


def transcribir(audio):
    segmentos, _ = modelo.transcribe(audio, language="es", vad_filter=True)
    return " ".join(s.text for s in segmentos).strip()


def preguntar(mensaje):
    try:
        r = requests.post(WEBHOOK_URL, json={"mensaje": mensaje}, timeout=180)
        r.raise_for_status()
        return r.json().get("respuesta", "(sin respuesta)")
    except Exception:
        return None


def main():
    print("\nJARVIS VOZ - Enter para hablar | q + Enter para salir")
    hablar("Jarvis en linea")
    while True:
        try:
            entrada = input("\n[Enter = hablar | q = salir] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if entrada == "q":
            hablar("Hasta luego, Juan")
            break
        audio = grabar()
        if audio.size == 0:
            print("No se grabo nada. Espera un segundo y presiona Enter otra vez.")
            continue
        print("Transcribiendo...")
        texto = transcribir(audio)
        if not texto:
            print("No te escuche bien, intenta de nuevo")
            continue
        print(f"Tu dijiste: {texto}")
        print("Jarvis esta pensando...")
        respuesta = preguntar(texto)
        if respuesta is None:
            print("No puedo conectar con n8n. Esta corriendo?")
            continue
        print(f"Jarvis: {respuesta}")
        hablar(respuesta)


if __name__ == "__main__":
    sys.exit(main())

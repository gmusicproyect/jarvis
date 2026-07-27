#!/usr/bin/env python3
"""JARVIS PRO - 'Hey Jarvis' o doble aplauso + voz neuronal en memoria."""

import subprocess
import sys
import time

import numpy as np
import requests
import sounddevice as sd

WEBHOOK_URL = "http://localhost:5678/webhook/jarvis"
KOKORO_MODEL = "mlx-community/Kokoro-82M-bf16"
KOKORO_VOZ = "em_alex"
MODELO_WHISPER = "small"
SAMPLE_RATE = 16000
CHUNK = 1280              # 80 ms por bloque
UMBRAL_WAKE = 0.6         # confianza minima de la palabra clave
UMBRAL_APLAUSO = 15000    # volumen tipico de un aplauso cerca del micro
UMBRAL_VOZ = 1000         # volumen minimo para considerar que hablas
SILENCIO_MAX_S = 1.4      # silencio que marca el fin de tu orden
ESPERA_VOZ_S = 5.0        # max espera a que empieces a hablar tras el ding
MAX_ORDEN_S = 15.0        # duracion maxima de una orden
SONIDO_DING = "/System/Library/Sounds/Ping.aiff"

print("Cargando oidos de Jarvis (Whisper)...")
from faster_whisper import WhisperModel
whisper = WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")

print("Cargando detector de 'Hey Jarvis'...")
from openwakeword.model import Model
detector = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

print("Cargando voz neuronal (Kokoro) en memoria...")
from mlx_audio.tts.utils import load_model
kokoro = load_model(model_path=KOKORO_MODEL)
print("Voz lista.")


def ding():
    print("ding!")
    subprocess.run(["afplay", "-v", "2", SONIDO_DING], check=False)


def hablar(texto):
    """Kokoro en memoria: voz neuronal casi inmediata, con respaldo."""
    try:
        texto_split = texto.replace(". ", ".\n")
        kwargs = dict(text=texto_split, voice=KOKORO_VOZ, speed=1.0, lang_code="e")
        try:
            resultados = kokoro.generate(**kwargs, verbose=False)
        except TypeError:
            resultados = kokoro.generate(**kwargs)
        for r in resultados:
            audio = np.array(r.audio, dtype=np.float32)
            sd.play(audio, samplerate=kokoro.sample_rate)
            sd.wait()
    except Exception as e:
        print("Kokoro fallo:", repr(e))
        subprocess.run(["say", texto], check=False)


def grabar_orden(stream):
    """Graba tu orden: empieza cuando hablas, termina con tu silencio."""
    detector.reset()
    stream.abort()   # limpia la cola del aplauso y del ding
    stream.start()
    time.sleep(0.2)
    frames = []
    silencio = 0.0
    empezo = False
    t0 = time.time()
    while True:
        data, _ = stream.read(CHUNK)
        audio = np.squeeze(data)
        frames.append(audio)
        vol = int(np.abs(audio).max())
        t = time.time() - t0
        if vol > UMBRAL_VOZ:
            empezo = True
            silencio = 0.0
        else:
            silencio += CHUNK / SAMPLE_RATE
        if not empezo and t > ESPERA_VOZ_S:
            return None
        if empezo and silencio > SILENCIO_MAX_S:
            break
        if t > MAX_ORDEN_S:
            break
    return np.concatenate(frames).astype(np.float32) / 32768.0


def transcribir(audio):
    segmentos, _ = whisper.transcribe(audio, language="es", vad_filter=True)
    return " ".join(s.text for s in segmentos).strip()


def preguntar(mensaje):
    try:
        r = requests.post(WEBHOOK_URL, json={"mensaje": mensaje}, timeout=180)
        r.raise_for_status()
        return r.json().get("respuesta", "(sin respuesta)")
    except Exception:
        return None


def main():
    print("\nJARVIS PRO listo. Di 'Hey Jarvis' o aplaude 2 veces (Ctrl+C para salir)\n")
    hablar("Jarvis en linea, senor.")
    print("(Escuchando... di 'Hey Jarvis' o aplaude 2 veces)")
    aplausos = []
    ultimo_pico = 0.0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="int16", blocksize=CHUNK) as stream:
        while True:
            data, _ = stream.read(CHUNK)
            audio = np.squeeze(data)
            vol = int(np.abs(audio).max())
            ahora = time.time()
            if vol > UMBRAL_APLAUSO and (ahora - ultimo_pico) > 0.25:
                ultimo_pico = ahora
                aplausos = [t for t in aplausos if ahora - t < 1.5] + [ahora]
                print(f"Aplauso! ({len(aplausos)} de 2)")
            score = detector.predict(audio)["hey_jarvis"]
            if score > UMBRAL_WAKE or len(aplausos) >= 2:
                aplausos = []
                print(f"\n>>> Activado (wake: {score:.2f})")
                ding()
                print("Escuchando tu orden...")
                audio_orden = grabar_orden(stream)
                detector.reset()
                if audio_orden is None:
                    print("No escuche nada. Aqui sigo.")
                    continue
                print("Transcribiendo...")
                texto = transcribir(audio_orden)
                if not texto:
                    print("No te entendi. Intenta otra vez.")
                    continue
                print(f"Tu dijiste: {texto}")
                print("Jarvis esta pensando...")
                respuesta = preguntar(texto)
                if respuesta is None:
                    stream.abort()
                    hablar("No puedo conectar con mi sistema nervioso, senor.")
                    stream.start()
                    continue
                print(f"Jarvis: {respuesta}")
                stream.abort()      # pausa el micro para no escucharse a si mismo
                hablar(respuesta)
                stream.start()      # reanuda la escucha con buffer limpio
                detector.reset()
                print("\n(Escuchando... di 'Hey Jarvis' o aplaude 2 veces)")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nJarvis fuera de linea. Hasta luego, Juan.")

#!/usr/bin/env python3
"""Diagnostico del detector 'Hey Jarvis' - muestra volumen y score en vivo."""
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

print("Cargando detector...")
model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

CHUNK = 1280
n = 0
print("\nDi 'HEY JARVIS' (J inglesa, como 'jungle')  (Ctrl+C para salir)\n")

with sd.InputStream(samplerate=16000, channels=1, dtype="int16",
                    blocksize=CHUNK) as stream:
    while True:
        data, _ = stream.read(CHUNK)
        audio = np.squeeze(data)
        score = model.predict(audio)["hey_jarvis"]
        vol = int(np.abs(audio).max())
        n += 1
        if n % 12 == 0:  # ~cada segundo
            print(f"vol: {vol:6d} | score: {score:.3f}")
        if score > 0.3:
            print(f">>> POSIBLE DETECCION: {score:.3f} <<<")

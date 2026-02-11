#!/usr/bin/env python3
"""Debug script to test wake word detection on a recorded wav file."""
import numpy as np
from scipy import signal as scipy_signal
import scipy.io.wavfile as wav
from openwakeword.model import Model

rate, data = wav.read("test.wav")
print(f"Original: {len(data)} samples, rate={rate}, max={np.max(np.abs(data))}")

resampled = scipy_signal.resample_poly(data, up=16000, down=44100).astype(np.int16)
print(f"Resampled: {len(resampled)} samples, max={np.max(np.abs(resampled))}")

model = Model(
    wakeword_models=["lightbulb/models/i_have_an_idea.onnx"],
    inference_framework="onnx",
)

for i in range(0, len(resampled) - 1280, 1280):
    chunk = resampled[i : i + 1280]
    pred = model.predict(chunk)
    for name, score in pred.items():
        if score > 0.01:
            print(f"  Chunk {i // 1280}: {name} = {score:.3f}")

print("Done")

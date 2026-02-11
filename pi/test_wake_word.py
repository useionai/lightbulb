#!/usr/bin/env python3
"""Simple wake word test script for ONNX model.

Works on both Mac and Raspberry Pi.
Usage: python test_wake_word.py
"""

import sys
import signal
import time
from pathlib import Path

# Configuration
THRESHOLD = 0.3  # Adjust 0.0-1.0 (lower = more sensitive)
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms at 16kHz

# Model search paths (in order of preference)
MODEL_SEARCH_PATHS = [
    Path(__file__).parent / "lightbulb/models/i_have_an_idea.onnx",  # Deployed location
    Path(__file__).parent / "../training/output/i_have_an_idea.onnx",  # Training output
]


def find_model() -> Path | None:
    """Find the model file in known locations."""
    for path in MODEL_SEARCH_PATHS:
        resolved = path.resolve()
        if resolved.exists():
            return resolved
    return None


def main():
    print("=" * 50)
    print("Wake Word Test Script")
    print("=" * 50)
    print(f"Threshold: {THRESHOLD}")
    print()

    # Find model
    MODEL_PATH = find_model()
    if MODEL_PATH is None:
        print("ERROR: Model not found in any of these locations:")
        for path in MODEL_SEARCH_PATHS:
            print(f"  - {path.resolve()}")
        sys.exit(1)
    print(f"Model: {MODEL_PATH}")
    print(f"Model file size: {MODEL_PATH.stat().st_size / 1024:.1f} KB")

    # Import dependencies
    print("\nLoading dependencies...")
    try:
        import numpy as np
        print("  numpy: OK")
    except ImportError as e:
        print(f"  ERROR: numpy not installed - {e}")
        sys.exit(1)

    try:
        import pyaudio
        print("  pyaudio: OK")
    except ImportError as e:
        print(f"  ERROR: pyaudio not installed - {e}")
        print("  Install with: pip install pyaudio")
        print("  On Mac: brew install portaudio && pip install pyaudio")
        sys.exit(1)

    try:
        from openwakeword.model import Model
        print("  openwakeword: OK")
    except ImportError as e:
        print(f"  ERROR: openwakeword not installed - {e}")
        print("  Install with: pip install openwakeword")
        sys.exit(1)

    try:
        import onnxruntime
        print(f"  onnxruntime: OK (version {onnxruntime.__version__})")
    except ImportError as e:
        print(f"  ERROR: onnxruntime not installed - {e}")
        print("  Install with: pip install onnxruntime")
        sys.exit(1)

    # List audio devices
    print("\nAudio input devices:")
    pa = pyaudio.PyAudio()
    default_device = None
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            marker = ""
            if default_device is None:
                default_device = i
                marker = " [USING]"
            print(f"  [{i}] {info['name']} ({int(info['maxInputChannels'])} ch){marker}")

    if default_device is None:
        print("  ERROR: No audio input devices found!")
        pa.terminate()
        sys.exit(1)

    # Determine recording sample rate (device may not support 16kHz)
    device_info = pa.get_device_info_by_index(default_device)
    device_rate = SAMPLE_RATE
    needs_resample = False
    try:
        pa.is_format_supported(
            SAMPLE_RATE,
            input_device=default_device,
            input_channels=1,
            input_format=pyaudio.paInt16,
        )
    except ValueError:
        device_rate = int(device_info["defaultSampleRate"])
        needs_resample = True
        print(f"\n  Device doesn't support {SAMPLE_RATE} Hz, recording at {device_rate} Hz and resampling")

    device_chunk_size = int(CHUNK_SIZE * device_rate / SAMPLE_RATE)

    # Load model
    print("\nLoading wake word model...")
    try:
        oww_model = Model(
            wakeword_models=[str(MODEL_PATH)],
            inference_framework="onnx",
        )
        print("  Model loaded successfully!")
        print(f"  Model names: {list(oww_model.models.keys())}")
    except Exception as e:
        print(f"  ERROR loading model: {e}")
        pa.terminate()
        sys.exit(1)

    # Open audio stream
    print("\nOpening audio stream...")
    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=device_rate,
            input=True,
            input_device_index=default_device,
            frames_per_buffer=device_chunk_size,
        )
        print(f"  Audio stream opened at {device_rate} Hz (chunk: {device_chunk_size})")
    except Exception as e:
        print(f"  ERROR opening audio stream: {e}")
        pa.terminate()
        sys.exit(1)

    # Setup signal handler for clean exit
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\n\nStopping...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Main loop
    print("\n" + "=" * 50)
    print("LISTENING... Say 'I have an idea'")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()

    detection_count = 0
    last_detection_time = 0
    cooldown = 2.0  # seconds

    try:
        while running:
            # Read audio chunk
            try:
                audio_data = stream.read(device_chunk_size, exception_on_overflow=False)
            except Exception as e:
                print(f"Audio read error: {e}")
                time.sleep(0.1)
                continue

            # Convert to numpy
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Resample if needed
            if needs_resample:
                from scipy.signal import resample_poly
                audio_array = resample_poly(
                    audio_array, up=SAMPLE_RATE, down=device_rate
                ).astype(np.int16)

            # Run prediction
            try:
                predictions = oww_model.predict(audio_array)
            except Exception as e:
                print(f"Prediction error: {e}")
                continue

            # Check predictions
            for model_name, score in predictions.items():
                # Show score for debugging
                if score > 0.01:
                    print(f"  Score: {score:.3f}", end="\r")

                if score >= THRESHOLD:
                    current_time = time.time()
                    if current_time - last_detection_time >= cooldown:
                        detection_count += 1
                        last_detection_time = current_time
                        print(f"\n{'*' * 50}")
                        print(f"* WAKE WORD DETECTED! (score: {score:.3f})")
                        print(f"* Detection #{detection_count}")
                        print(f"* Model: {model_name}")
                        print(f"{'*' * 50}\n")
                    else:
                        print(f"  [cooldown] score: {score:.3f}", end="\r")

    except Exception as e:
        print(f"\nError in main loop: {e}")

    # Cleanup
    print("\nCleaning up...")
    stream.stop_stream()
    stream.close()
    pa.terminate()
    print(f"Total detections: {detection_count}")
    print("Done!")


if __name__ == "__main__":
    main()

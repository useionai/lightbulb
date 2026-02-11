"""Audio device utilities."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def list_audio_devices() -> list[dict[str, Any]]:
    """List all available audio input devices.

    Returns:
        List of device info dictionaries.
    """
    try:
        import pyaudio

        pa = pyaudio.PyAudio()
        devices = []

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            # Only include input devices
            if info.get("maxInputChannels", 0) > 0:
                devices.append({
                    "index": i,
                    "name": info.get("name", "Unknown"),
                    "channels": info.get("maxInputChannels", 0),
                    "sample_rate": int(info.get("defaultSampleRate", 16000)),
                })

        pa.terminate()
        return devices

    except ImportError:
        logger.warning("PyAudio not available")
        return []
    except Exception as e:
        logger.error(f"Error listing audio devices: {e}")
        return []


def find_usb_microphone() -> int | None:
    """Find a USB microphone device index.

    Returns:
        Device index or None if not found.
    """
    devices = list_audio_devices()

    # Look for common USB microphone names
    usb_keywords = ["usb", "microphone", "mic", "audio"]

    for device in devices:
        name_lower = device["name"].lower()
        if any(kw in name_lower for kw in usb_keywords):
            logger.info(f"Found USB microphone: {device['name']} (index {device['index']})")
            return device["index"]

    # If no USB mic found, return the first input device
    if devices:
        logger.info(f"Using default input device: {devices[0]['name']}")
        return devices[0]["index"]

    logger.warning("No audio input devices found")
    return None


def test_microphone(device_index: int | None = None, duration: float = 2.0) -> bool:
    """Test if the microphone is working.

    Args:
        device_index: Audio device index (None for default).
        duration: Test duration in seconds.

    Returns:
        True if audio was captured successfully.
    """
    try:
        import pyaudio
        import numpy as np

        pa = pyaudio.PyAudio()

        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1280,
        )

        frames = []
        num_chunks = int(16000 * duration / 1280)

        for _ in range(num_chunks):
            data = stream.read(1280, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        pa.terminate()

        # Check if we got any audio
        audio_data = b"".join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Check if there's any variation (not just silence)
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

        if rms > 100:
            logger.info(f"Microphone test passed (RMS: {rms:.1f})")
            return True
        else:
            logger.warning(f"Microphone test: very low audio level (RMS: {rms:.1f})")
            return True  # Still technically working

    except Exception as e:
        logger.error(f"Microphone test failed: {e}")
        return False

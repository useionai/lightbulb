#!/usr/bin/env python3
"""Hardware test script for LED strip and microphone."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_leds():
    """Test the LED strip with a simple color cycle."""
    print("\n=== LED Strip Test ===")
    print("This test will cycle through colors on your LED strip.")

    try:
        from lightbulb.config import Config
        from lightbulb.led.controller import LEDController

        config = Config()
        led_config = config.led

        print(f"LED count: {led_config.get('count', 120)}")
        print(f"GPIO pin: {led_config.get('pin', 18)}")

        controller = LEDController(
            led_count=led_config.get("count", 120),
            pin=led_config.get("pin", 18),
            brightness=led_config.get("brightness", 255),
        )

        colors = [
            ("Red", 255, 0, 0),
            ("Green", 0, 255, 0),
            ("Blue", 0, 0, 255),
            ("Yellow", 255, 255, 0),
            ("White", 255, 255, 255),
        ]

        for name, r, g, b in colors:
            print(f"  Setting all LEDs to {name}...")
            controller.set_all(r, g, b)
            time.sleep(1)

        print("  Testing rainbow scene...")
        controller.apply_scene("rainbow")
        time.sleep(2)

        print("  Turning off LEDs...")
        controller.clear()

        print("LED test PASSED")
        return True

    except Exception as e:
        print(f"LED test FAILED: {e}")
        return False


def test_microphone():
    """Test the USB microphone."""
    print("\n=== Microphone Test ===")
    print("This test will record 2 seconds of audio.")

    try:
        from lightbulb.wake_word.audio import (
            list_audio_devices,
            find_usb_microphone,
            test_microphone,
        )

        print("\nAvailable audio input devices:")
        devices = list_audio_devices()
        if not devices:
            print("  No audio input devices found!")
            return False

        for device in devices:
            print(f"  [{device['index']}] {device['name']}")

        device_index = find_usb_microphone()
        if device_index is not None:
            print(f"\nUsing device index: {device_index}")
            print("Recording 2 seconds of audio...")

            if test_microphone(device_index, duration=2.0):
                print("Microphone test PASSED")
                return True
            else:
                print("Microphone test FAILED: No audio detected")
                return False
        else:
            print("No microphone found")
            return False

    except Exception as e:
        print(f"Microphone test FAILED: {e}")
        return False


def test_wake_word_model():
    """Check if the wake word model exists."""
    print("\n=== Wake Word Model Check ===")

    try:
        from lightbulb.config import Config

        config = Config()
        wake_config = config.wake_word
        model_path = Path(wake_config.get("model_path", "lightbulb/models/i_have_an_idea.tflite"))

        # Check relative to project root
        if not model_path.is_absolute():
            model_path = project_root / model_path

        if model_path.exists():
            print(f"Wake word model found: {model_path}")
            print("Wake word model check PASSED")
            return True
        else:
            print(f"Wake word model NOT found: {model_path}")
            print("See docs/WAKE_WORD_TRAINING.md for training instructions.")
            print("Wake word model check SKIPPED (model not required for basic operation)")
            return True  # Not a failure, just not configured yet

    except Exception as e:
        print(f"Wake word model check FAILED: {e}")
        return False


def main():
    """Run all hardware tests."""
    print("=" * 50)
    print("Lightbulb Hardware Test")
    print("=" * 50)

    results = {
        "LED Strip": test_leds(),
        "Microphone": test_microphone(),
        "Wake Word Model": test_wake_word_model(),
    }

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

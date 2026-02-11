"""Main entry point for Lightbulb application."""

import logging
import signal
import sys
from pathlib import Path

from lightbulb.config import Config
from lightbulb.led.controller import LEDController
from lightbulb.api.app import create_app
from lightbulb.wake_word.listener import WakeWordListener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def on_wake_word_detected(controller: LEDController) -> None:
    """Callback when wake word is detected."""
    logger.info("Wake word detected! Turning lights yellow...")
    controller.set_all(255, 255, 0)  # Yellow


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    logger.info("Starting Lightbulb...")

    # Load configuration
    try:
        config = Config()
        logger.info("Configuration loaded")
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Initialize LED controller
    led_config = config.led
    controller = LEDController(
        led_count=led_config.get("count", 120),
        pin=led_config.get("pin", 18),
        brightness=led_config.get("brightness", 255),
    )

    # Clear LEDs on startup
    controller.clear()
    logger.info("LED controller ready")

    # Initialize wake word listener
    wake_config = config.wake_word
    model_path = Path(wake_config.get("model_path", "lightbulb/models/i_have_an_idea.onnx"))
    if not model_path.is_absolute():
        # Resolve relative to the project root (parent of lightbulb package)
        model_path = Path(__file__).parent.parent / model_path

    wake_listener = None
    logger.info(f"Looking for wake word model at: {model_path} (exists: {model_path.exists()})")
    if model_path.exists():
        audio_config = config.audio
        wake_listener = WakeWordListener(
            model_path=str(model_path),
            threshold=wake_config.get("threshold", 0.5),
            cooldown_seconds=wake_config.get("cooldown_seconds", 3.0),
            sample_rate=audio_config.get("sample_rate", 16000),
            chunk_size=audio_config.get("chunk_size", 1280),
            device_index=audio_config.get("device_index"),
            on_detection=lambda: on_wake_word_detected(controller),
        )

        if wake_listener.start():
            logger.info("Wake word listener started")
        else:
            logger.warning("Failed to start wake word listener")
            wake_listener = None
    else:
        logger.warning(
            f"Wake word model not found: {model_path}. "
            "Wake word detection disabled. "
            "See docs/WAKE_WORD_TRAINING.md for training instructions."
        )

    # Create Flask app
    app = create_app()
    api_config = config.api

    # Setup signal handlers for graceful shutdown
    def shutdown_handler(signum, frame):
        logger.info("Shutting down...")
        if wake_listener is not None:
            wake_listener.stop()
        controller.clear()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Run Flask app
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 5000)

    logger.info(f"Starting Flask server on {host}:{port}")
    logger.info(f"API available at http://{host}:{port}/api/")

    try:
        # Use threaded=True to handle multiple requests
        # use_reloader=False because we're managing our own threads
        app.run(
            host=host,
            port=port,
            threaded=True,
            use_reloader=False,
        )
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        return 1
    finally:
        if wake_listener is not None:
            wake_listener.stop()
        controller.clear()

    return 0


if __name__ == "__main__":
    sys.exit(main())

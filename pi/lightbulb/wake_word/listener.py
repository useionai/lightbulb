"""Wake word listener using openWakeWord."""

import logging
import threading
import time
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.signal import resample_poly

logger = logging.getLogger(__name__)


class WakeWordListener:
    """Listens for wake word and triggers callback on detection."""

    def __init__(
        self,
        model_path: str,
        threshold: float = 0.5,
        cooldown_seconds: float = 3.0,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
        device_index: int | None = None,
        on_detection: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the wake word listener.

        Args:
            model_path: Path to the .tflite wake word model.
            threshold: Detection threshold (0.0-1.0).
            cooldown_seconds: Minimum time between detections.
            sample_rate: Audio sample rate (should be 16000 for openWakeWord).
            chunk_size: Audio chunk size (1280 = 80ms at 16kHz).
            device_index: Audio device index (None for default).
            on_detection: Callback function when wake word is detected.
        """
        self._model_path = Path(model_path)
        self._threshold = threshold
        self._cooldown_seconds = cooldown_seconds
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._device_index = device_index
        self._on_detection = on_detection

        self._running = False
        self._thread: threading.Thread | None = None
        self._last_detection: float = 0.0

        self._oww_model = None
        self._pyaudio = None
        self._stream = None
        self._device_rate: int | None = None

    def _init_model(self) -> bool:
        """Initialize the openWakeWord model.

        Returns:
            True if initialization succeeded.
        """
        try:
            from openwakeword.model import Model

            if not self._model_path.exists():
                logger.error(f"Wake word model not found: {self._model_path}")
                return False

            self._oww_model = Model(
                wakeword_models=[str(self._model_path)],
                inference_framework="onnx",
            )

            logger.info(f"Loaded wake word model: {self._model_path}")
            return True

        except ImportError:
            logger.error("openwakeword not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")
            return False

    def _init_audio(self) -> bool:
        """Initialize the audio stream.

        Records at the device's native sample rate and resamples to
        the target rate (16kHz) if needed.

        Returns:
            True if initialization succeeded.
        """
        try:
            import pyaudio

            self._pyaudio = pyaudio.PyAudio()

            # Check if device supports target sample rate directly
            device_info = self._pyaudio.get_device_info_by_index(
                self._device_index or 0
            )
            self._device_rate = self._sample_rate

            try:
                self._pyaudio.is_format_supported(
                    self._sample_rate,
                    input_device=self._device_index or 0,
                    input_channels=1,
                    input_format=pyaudio.paInt16,
                )
            except ValueError:
                # Device doesn't support target rate, use its native rate
                self._device_rate = int(device_info["defaultSampleRate"])
                logger.info(
                    f"Device doesn't support {self._sample_rate} Hz, "
                    f"recording at {self._device_rate} Hz and resampling"
                )

            # Scale chunk size to match device rate so we get the same
            # duration of audio per read
            self._device_chunk_size = int(
                self._chunk_size * self._device_rate / self._sample_rate
            )

            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._device_rate,
                input=True,
                input_device_index=self._device_index,
                frames_per_buffer=self._device_chunk_size,
            )

            logger.info(
                f"Audio stream initialized at {self._device_rate} Hz "
                f"(chunk: {self._device_chunk_size})"
            )
            return True

        except ImportError:
            logger.error("PyAudio not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            return False

    def _cleanup(self) -> None:
        """Clean up audio resources."""
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

    def _listen_loop(self) -> None:
        """Main listening loop (runs in background thread)."""
        # Initialize model and audio in this thread
        if not self._init_model():
            self._start_error = True
            return
        if not self._init_audio():
            self._start_error = True
            return

        logger.info("Wake word listener started")
        chunk_count = 0

        while self._running:
            try:
                # Read audio chunk
                audio_data = self._stream.read(
                    self._device_chunk_size,
                    exception_on_overflow=False,
                )
                chunk_count += 1
                t_read = time.time()

                if chunk_count <= 3 or chunk_count % 100 == 0:
                    audio_peek = np.frombuffer(audio_data, dtype=np.int16)
                    logger.info(
                        f"Chunk #{chunk_count}: len={len(audio_peek)}, "
                        f"max={np.max(np.abs(audio_peek))}"
                    )

                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Resample if device rate differs from target rate
                if self._device_rate != self._sample_rate:
                    audio_array = resample_poly(
                        audio_array, up=self._sample_rate, down=self._device_rate
                    ).astype(np.int16)

                # Run prediction
                prediction = self._oww_model.predict(audio_array)
                t_predict = time.time()

                if chunk_count <= 5:
                    logger.info(
                        f"Chunk #{chunk_count} timing: "
                        f"resample+predict={t_predict - t_read:.3f}s, "
                        f"predictions={prediction}"
                    )

                # Check for detection
                for model_name, score in prediction.items():
                    if score > 0.01:
                        logger.info(f"Score: {model_name} = {score:.3f}")
                    if score >= self._threshold:
                        current_time = time.time()

                        # Check cooldown
                        if current_time - self._last_detection >= self._cooldown_seconds:
                            self._last_detection = current_time
                            logger.info(
                                f"Wake word detected: {model_name} "
                                f"(score: {score:.3f})"
                            )

                            # Trigger callback
                            if self._on_detection is not None:
                                try:
                                    self._on_detection()
                                except Exception as e:
                                    logger.error(f"Error in detection callback: {e}")
                        else:
                            logger.debug(
                                f"Wake word detected but in cooldown "
                                f"(score: {score:.3f})"
                            )

            except Exception as e:
                if self._running:
                    logger.error(f"Error in listen loop: {e}")
                    time.sleep(0.1)  # Brief pause before retry

        logger.info("Wake word listener stopped")

    def start(self) -> bool:
        """Start the wake word listener in a background thread.

        Model and audio are initialized inside the thread to avoid
        cross-thread issues with onnxruntime and openWakeWord state.

        Returns:
            True if started successfully.
        """
        if self._running:
            logger.warning("Listener already running")
            return True

        # Start background thread (model + audio init happens inside)
        self._running = True
        self._start_error = False
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

        # Wait briefly for initialization
        for _ in range(100):
            if self._oww_model is not None or self._start_error:
                break
            time.sleep(0.1)

        if self._start_error:
            self._running = False
            return False

        return True

    def stop(self) -> None:
        """Stop the wake word listener."""
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._cleanup()

    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._running

    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set the detection callback.

        Args:
            callback: Function to call when wake word is detected.
        """
        self._on_detection = callback

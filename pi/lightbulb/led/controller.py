"""Thread-safe LED controller for WS281x LED strips."""

import logging
import threading
from typing import Any

from lightbulb.led.colors import Color, OFF
from lightbulb.led.scenes import SCENES, get_scene
from lightbulb.led.animator import Animator, get_animated_scene, list_animated_scenes

logger = logging.getLogger(__name__)


class LEDController:
    """Thread-safe controller for WS281x LED strips.

    This is implemented as a singleton to ensure only one instance
    controls the LED strip at a time.
    """

    _instance: "LEDController | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "LEDController":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        led_count: int = 120,
        pin: int = 18,
        brightness: int = 255,
        simulate: bool = False,
    ) -> None:
        """Initialize the LED controller.

        Args:
            led_count: Number of LEDs in the strip.
            pin: GPIO pin number (must support PWM, typically 18 or 12).
            brightness: Global brightness (0-255).
            simulate: If True, simulate LEDs without hardware (for testing).
        """
        if self._initialized:
            return

        self._led_count = led_count
        self._pin = pin
        self._brightness = brightness
        self._simulate = simulate
        self._operation_lock = threading.Lock()

        # Current state: list of Color objects
        self._state: list[Color] = [OFF] * led_count
        self._current_scene: str | None = None

        # Animator for animated scenes
        self._animator = Animator()

        # Initialize hardware
        self._strip = None
        if not simulate:
            self._init_hardware()

        self._initialized = True
        logger.info(
            f"LED controller initialized: {led_count} LEDs on pin {pin}, "
            f"brightness={brightness}, simulate={simulate}"
        )

    def _init_hardware(self) -> None:
        """Initialize the WS281x hardware."""
        try:
            from rpi_ws281x import PixelStrip, WS2811_STRIP_GRB

            self._strip = PixelStrip(
                num=self._led_count,
                pin=self._pin,
                freq_hz=800000,
                dma=10,
                invert=False,
                brightness=self._brightness,
                channel=0,
                strip_type=WS2811_STRIP_GRB,
            )
            self._strip.begin()
            logger.info("Hardware initialized successfully")
        except ImportError:
            logger.warning(
                "rpi_ws281x not available, running in simulation mode"
            )
            self._simulate = True
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            logger.warning("Falling back to simulation mode")
            self._simulate = True

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """Set a single pixel to an RGB color.

        Args:
            index: LED index (0-based).
            r: Red value (0-255).
            g: Green value (0-255).
            b: Blue value (0-255).
        """
        if not 0 <= index < self._led_count:
            raise ValueError(f"Index {index} out of range (0-{self._led_count - 1})")

        # Stop any running animation
        self._animator.stop()

        color = Color(r, g, b)

        with self._operation_lock:
            self._state[index] = color
            self._current_scene = None  # Manual change clears scene

            if self._strip is not None:
                # rpi_ws281x uses 24-bit color
                self._strip.setPixelColor(index, (r << 16) | (g << 8) | b)
                self._strip.show()

            logger.debug(f"Set pixel {index} to ({r}, {g}, {b})")

    def set_all(self, r: int, g: int, b: int) -> None:
        """Set all pixels to the same RGB color.

        Args:
            r: Red value (0-255).
            g: Green value (0-255).
            b: Blue value (0-255).
        """
        # Stop any running animation
        self._animator.stop()

        color = Color(r, g, b)

        with self._operation_lock:
            self._state = [color] * self._led_count
            self._current_scene = None

            if self._strip is not None:
                color_value = (r << 16) | (g << 8) | b
                for i in range(self._led_count):
                    self._strip.setPixelColor(i, color_value)
                self._strip.show()

            logger.debug(f"Set all {self._led_count} pixels to ({r}, {g}, {b})")

    def _set_all_direct(self, r: int, g: int, b: int) -> None:
        """Set all pixels directly without stopping animations.

        This is used internally by the animator.
        """
        color = Color(r, g, b)

        with self._operation_lock:
            self._state = [color] * self._led_count

            if self._strip is not None:
                color_value = (r << 16) | (g << 8) | b
                for i in range(self._led_count):
                    self._strip.setPixelColor(i, color_value)
                self._strip.show()

    def _set_colors_direct(self, colors: list[Color]) -> None:
        """Set all pixels to individual colors without stopping animations.

        This is used internally by the animator for wave effects.
        """
        with self._operation_lock:
            self._state = colors

            if self._strip is not None:
                for i, color in enumerate(colors):
                    color_value = (color.r << 16) | (color.g << 8) | color.b
                    self._strip.setPixelColor(i, color_value)
                self._strip.show()

    def apply_scene(self, name: str) -> bool:
        """Apply a predefined scene to the LED strip.

        This handles both static and animated scenes.

        Args:
            name: Scene name (static or animated).

        Returns:
            True if scene was applied, False if scene not found.
        """
        # Check if it's an animated scene first
        if get_animated_scene(name) is not None:
            return self._apply_animated_scene(name)

        # Stop any running animation for static scenes
        self._animator.stop()

        scene_func = get_scene(name)
        if scene_func is None:
            logger.warning(f"Scene not found: {name}")
            return False

        colors = scene_func(self._led_count)

        with self._operation_lock:
            self._state = colors
            self._current_scene = name

            if self._strip is not None:
                for i, color in enumerate(colors):
                    color_value = (color.r << 16) | (color.g << 8) | color.b
                    self._strip.setPixelColor(i, color_value)
                self._strip.show()

            logger.info(f"Applied scene: {name}")

        return True

    def _apply_animated_scene(self, name: str) -> bool:
        """Start an animated scene.

        Args:
            name: Animated scene name.

        Returns:
            True if animation started, False if scene not found.
        """
        with self._operation_lock:
            self._current_scene = name

        if self._animator.start(name, self):
            logger.info(f"Started animated scene: {name}")
            return True
        return False

    def clear(self) -> None:
        """Turn off all LEDs."""
        self.apply_scene("off")

    def get_state(self) -> dict[str, Any]:
        """Get the current state of all LEDs.

        Returns:
            Dictionary containing LED states and current scene.
        """
        with self._operation_lock:
            return {
                "led_count": self._led_count,
                "brightness": self._brightness,
                "current_scene": self._current_scene,
                "animated": self._animator.is_running(),
                "leds": [
                    {"index": i, "r": c.r, "g": c.g, "b": c.b}
                    for i, c in enumerate(self._state)
                ],
            }

    def get_pixel(self, index: int) -> dict[str, int]:
        """Get the color of a single pixel.

        Args:
            index: LED index (0-based).

        Returns:
            Dictionary with r, g, b values.
        """
        if not 0 <= index < self._led_count:
            raise ValueError(f"Index {index} out of range (0-{self._led_count - 1})")

        with self._operation_lock:
            color = self._state[index]
            return {"r": color.r, "g": color.g, "b": color.b}

    def set_brightness(self, brightness: int) -> None:
        """Set the global brightness.

        Args:
            brightness: Brightness value (0-255).
        """
        if not 0 <= brightness <= 255:
            raise ValueError(f"Brightness must be 0-255, got {brightness}")

        with self._operation_lock:
            self._brightness = brightness
            if self._strip is not None:
                self._strip.setBrightness(brightness)
                self._strip.show()
            logger.info(f"Brightness set to {brightness}")

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._animator.stop()
                cls._instance.clear()
            cls._instance = None

    def get_all_scenes(self) -> list[str]:
        """Get list of all available scenes (static and animated)."""
        from lightbulb.led.scenes import list_scenes
        return list_scenes() + list_animated_scenes()

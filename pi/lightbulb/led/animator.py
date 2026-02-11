"""Background animator for LED color fading effects."""

import logging
import threading
import time
from dataclasses import dataclass

from lightbulb.led.colors import Color, lerp_color

logger = logging.getLogger(__name__)


@dataclass
class AnimatedScene:
    """Definition of an animated scene that fades between colors.

    The wave spreads across the strip so each LED is at a different
    point in the color cycle, creating a flowing effect.
    """

    name: str
    colors: list[Color]
    cycle_duration: float = 10.0  # seconds for full color cycle
    wave_spread: float = 1.0  # how much of the color cycle is visible across strip (1.0 = full cycle)
    fps: int = 30  # frames per second


# Animated scene definitions
ANIMATED_SCENES: dict[str, AnimatedScene] = {
    "dreamy": AnimatedScene(
        name="dreamy",
        colors=[
            Color(70, 130, 230),   # blue
            Color(138, 43, 226),   # purple
            Color(255, 105, 180),  # pink
            Color(186, 85, 211),   # medium orchid
        ],
        cycle_duration=12.0,
        wave_spread=0.5,
    ),
}


class Animator:
    """Background thread animator for LED strips."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_scene: str | None = None
        self._controller = None

    def start(self, scene_name: str, controller: "LEDController") -> bool:
        """Start an animated scene.

        Args:
            scene_name: Name of the animated scene.
            controller: LED controller instance.

        Returns:
            True if animation started, False if scene not found.
        """
        if scene_name not in ANIMATED_SCENES:
            return False

        self.stop()

        self._controller = controller
        self._current_scene = scene_name
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_animation,
            args=(ANIMATED_SCENES[scene_name],),
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Started animated scene: {scene_name}")
        return True

    def stop(self) -> None:
        """Stop the current animation."""
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)
            logger.info(f"Stopped animated scene: {self._current_scene}")

        self._thread = None
        self._current_scene = None
        self._controller = None

    def is_running(self) -> bool:
        """Check if an animation is currently running."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def current_scene(self) -> str | None:
        """Get the name of the currently running animated scene."""
        return self._current_scene if self.is_running() else None

    def _run_animation(self, scene: AnimatedScene) -> None:
        """Animation loop that creates a flowing wave of colors across the strip."""
        frame_time = 1.0 / scene.fps
        color_count = len(scene.colors)

        while not self._stop_event.is_set():
            if self._controller is None:
                break

            led_count = self._controller._led_count
            elapsed = time.time()

            # Base position in the color cycle (0.0 to color_count)
            base_position = (elapsed % scene.cycle_duration) / scene.cycle_duration * color_count

            # Calculate color for each LED
            colors = []
            for i in range(led_count):
                # Each LED is offset based on its position in the strip
                led_offset = (i / led_count) * scene.wave_spread * color_count
                position = (base_position + led_offset) % color_count

                color_index = int(position)
                next_color_index = (color_index + 1) % color_count
                t = position - color_index

                color = lerp_color(
                    scene.colors[color_index],
                    scene.colors[next_color_index],
                    t,
                )
                colors.append(color)

            # Apply colors to all LEDs
            self._controller._set_colors_direct(colors)

            # Wait for next frame
            self._stop_event.wait(frame_time)


def get_animated_scene(name: str) -> AnimatedScene | None:
    """Get an animated scene by name."""
    return ANIMATED_SCENES.get(name)


def list_animated_scenes() -> list[str]:
    """List all available animated scene names."""
    return list(ANIMATED_SCENES.keys())

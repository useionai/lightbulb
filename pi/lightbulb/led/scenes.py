"""Scene definitions for LED strips."""

from typing import Callable

from lightbulb.led.colors import (
    OFF, RED, GREEN, BLUE, YELLOW, WHITE,
    WARM_WHITE, COOL_WHITE, Color, wheel
)


# Scene type: function that takes led_count and returns list of Color objects
SceneFunc = Callable[[int], list[Color]]


def scene_off(led_count: int) -> list[Color]:
    """All LEDs off."""
    return [OFF] * led_count


def scene_all_red(led_count: int) -> list[Color]:
    """All LEDs red."""
    return [RED] * led_count


def scene_all_green(led_count: int) -> list[Color]:
    """All LEDs green."""
    return [GREEN] * led_count


def scene_all_blue(led_count: int) -> list[Color]:
    """All LEDs blue."""
    return [BLUE] * led_count


def scene_all_yellow(led_count: int) -> list[Color]:
    """All LEDs yellow."""
    return [YELLOW] * led_count


def scene_all_white(led_count: int) -> list[Color]:
    """All LEDs white."""
    return [WHITE] * led_count


def scene_warm_white(led_count: int) -> list[Color]:
    """All LEDs warm white (~2700K)."""
    return [WARM_WHITE] * led_count


def scene_cool_white(led_count: int) -> list[Color]:
    """All LEDs cool white (~6500K)."""
    return [COOL_WHITE] * led_count


def scene_rainbow(led_count: int) -> list[Color]:
    """Rainbow gradient across the strip."""
    colors = []
    for i in range(led_count):
        pos = int(i * 256 / led_count)
        r, g, b = wheel(pos)
        colors.append(Color(r, g, b))
    return colors


def scene_idea(led_count: int) -> list[Color]:
    """Yellow 'idea' scene - triggered by wake word."""
    return [YELLOW] * led_count


# Registry of all available scenes
SCENES: dict[str, SceneFunc] = {
    "off": scene_off,
    "all_red": scene_all_red,
    "all_green": scene_all_green,
    "all_blue": scene_all_blue,
    "all_yellow": scene_all_yellow,
    "all_white": scene_all_white,
    "warm_white": scene_warm_white,
    "cool_white": scene_cool_white,
    "rainbow": scene_rainbow,
    "idea": scene_idea,
}


def get_scene(name: str) -> SceneFunc | None:
    """Get a scene function by name.

    Args:
        name: Scene name.

    Returns:
        Scene function or None if not found.
    """
    return SCENES.get(name)


def list_scenes() -> list[str]:
    """List all available scene names."""
    return list(SCENES.keys())

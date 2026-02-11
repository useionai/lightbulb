"""Color constants and utilities for LED control."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    """RGB color representation."""
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        """Validate color values are in range 0-255."""
        for attr in ("r", "g", "b"):
            value = getattr(self, attr)
            if not 0 <= value <= 255:
                raise ValueError(f"{attr} must be between 0 and 255, got {value}")

    def to_tuple(self) -> tuple[int, int, int]:
        """Return color as (r, g, b) tuple."""
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Return color as hex string (e.g., '#FF0000')."""
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create color from hex string (e.g., '#FF0000' or 'FF0000')."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        return cls(
            r=int(hex_str[0:2], 16),
            g=int(hex_str[2:4], 16),
            b=int(hex_str[4:6], 16),
        )


# Color constants
OFF = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
WHITE = Color(255, 255, 255)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
ORANGE = Color(255, 165, 0)
PURPLE = Color(128, 0, 128)

# Temperature-based whites
WARM_WHITE = Color(255, 244, 229)  # ~2700K
COOL_WHITE = Color(255, 255, 255)  # ~6500K
DAYLIGHT = Color(255, 250, 244)    # ~5000K


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex string."""
    return Color(r, g, b).to_hex()


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string to RGB tuple."""
    return Color.from_hex(hex_str).to_tuple()


def wheel(pos: int) -> tuple[int, int, int]:
    """Generate rainbow colors across 0-255 positions.

    Args:
        pos: Position in the color wheel (0-255).

    Returns:
        Tuple of (r, g, b) values.
    """
    pos = pos % 256
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def lerp_color(color1: Color, color2: Color, t: float) -> Color:
    """Linearly interpolate between two colors.

    Args:
        color1: Starting color.
        color2: Ending color.
        t: Interpolation factor (0.0 = color1, 1.0 = color2).

    Returns:
        Interpolated color.
    """
    t = max(0.0, min(1.0, t))
    return Color(
        r=int(color1.r + (color2.r - color1.r) * t),
        g=int(color1.g + (color2.g - color1.g) * t),
        b=int(color1.b + (color2.b - color1.b) * t),
    )

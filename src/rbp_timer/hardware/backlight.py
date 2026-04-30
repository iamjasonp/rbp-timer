"""GFX HAT backlight color management."""

from __future__ import annotations

from typing import Tuple

try:
    from gfxhat import backlight
except ImportError:
    backlight = None


# State-to-color mapping (R, G, B)
# Timer states are at 50% brightness; menu is full brightness
COLORS = {
    "work": (0, 128, 0),
    "break": (0, 50, 128),
    "paused": (128, 100, 0),
    "done": (128, 0, 0),
    "menu": (80, 80, 80),
}


class Backlight:
    """Controls the GFX HAT RGB backlight zones."""

    def __init__(self):
        self._current_color: Tuple[int, int, int] = (0, 0, 0)

    def set_state(self, state: str) -> None:
        """Set backlight color based on a named state."""
        color = COLORS.get(state, COLORS["menu"])
        self.set_color(*color)

    def set_color(self, r: int, g: int, b: int) -> None:
        """Set all backlight zones to an RGB color."""
        self._current_color = (r, g, b)
        if backlight is None:
            return
        backlight.set_all(r, g, b)
        backlight.show()

    def off(self) -> None:
        """Turn off the backlight."""
        self.set_color(0, 0, 0)

    @property
    def current_color(self) -> Tuple[int, int, int]:
        return self._current_color

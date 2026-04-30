"""GFX HAT capacitive touch button input handling."""

from __future__ import annotations

import threading
from typing import Callable, Dict, Optional

try:
    from gfxhat import touch
except ImportError:
    touch = None

# Button index constants matching GFX HAT layout
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
A = 4
B = 5

BUTTON_NAMES = {UP: "up", DOWN: "down", LEFT: "left", RIGHT: "right", A: "a", B: "b"}


class Buttons:
    """Handles GFX HAT capacitive touch input and dispatches to callbacks."""

    def __init__(self):
        self._handlers: Dict[int, Callable[[], None]] = {}
        self._lock = threading.Lock()
        self._enabled = False

    def register(self, button: int, handler: Callable[[], None]) -> None:
        """Register a callback for a button press."""
        with self._lock:
            self._handlers[button] = handler

    def clear_handlers(self) -> None:
        """Remove all button handlers."""
        with self._lock:
            self._handlers.clear()

    def enable(self) -> None:
        """Start listening for button events on the hardware."""
        if touch is None or self._enabled:
            return
        self._enabled = True
        for btn in range(6):
            touch.on(btn, self._on_touch)
            touch.set_led(btn, 1)

    def disable(self) -> None:
        """Stop button LEDs (handlers remain registered)."""
        if touch is None:
            return
        for btn in range(6):
            touch.set_led(btn, 0)
        self._enabled = False

    def _on_touch(self, ch: int, event: str) -> None:
        """Internal touch event dispatcher."""
        if event != "press":
            return
        with self._lock:
            handler = self._handlers.get(ch)
        if handler:
            handler()

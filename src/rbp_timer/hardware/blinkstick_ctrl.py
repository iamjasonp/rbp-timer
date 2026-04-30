"""BlinkStick USB LED control with animations."""

from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

try:
    from blinkstick import blinkstick
except ImportError:
    blinkstick = None


# BlinkStick-specific color overrides (deeper blue looks better on LEDs)
BLINKSTICK_COLORS = {
    "work": (128, 0, 0),
    "break": (0, 0, 128),
    "paused": (128, 100, 0),
    "done": (0, 128, 0),
    "available": (0, 128, 0),
    "away": (128, 100, 0),
    "busy": (128, 0, 0),
}


class BlinkStickController:
    """Controls a BlinkStick USB LED with steady colors and animations."""

    # BlinkStick Square has 8 WS2812 LEDs
    _NUM_LEDS = 8
    # Global brightness scalar (0.0–1.0) applied to all color output
    _BRIGHTNESS = 0.25

    def __init__(self):
        self._stick = None
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_color: Tuple[int, int, int] = (0, 0, 0)

        if blinkstick:
            self._stick = blinkstick.find_first()
            if self._stick:
                try:
                    self._stick.set_mode(2)  # WS2812 mode
                except Exception:
                    pass

    @property
    def available(self) -> bool:
        return self._stick is not None

    def set_color(self, r: int, g: int, b: int) -> None:
        """Set a steady color, stopping any running animation."""
        self._stop_animation()
        self._current_color = (r, g, b)
        self._set_hw_color(r, g, b)

    def off(self) -> None:
        """Turn off the LED."""
        self.set_color(0, 0, 0)

    def pulse(self, r: int, g: int, b: int, duration: float = 3.0, speed: float = 0.02) -> None:
        """Start a pulsing animation in a background thread."""
        self._stop_animation()
        self._stop_event.clear()
        self._animation_thread = threading.Thread(
            target=self._pulse_loop, args=(r, g, b, duration, speed), daemon=True
        )
        self._animation_thread.start()

    def flash(self, r: int, g: int, b: int, count: int = 5, on_time: float = 0.15, off_time: float = 0.15) -> None:
        """Start a flashing animation then hold steady at the given color."""
        self._stop_animation()
        self._stop_event.clear()
        self._current_color = (r, g, b)
        self._animation_thread = threading.Thread(
            target=self._flash_loop, args=(r, g, b, count, on_time, off_time), daemon=True
        )
        self._animation_thread.start()

    def cleanup(self) -> None:
        """Turn off and release resources."""
        self._stop_animation()
        self._set_hw_color(0, 0, 0)

    def _set_hw_color(self, r: int, g: int, b: int) -> None:
        if self._stick:
            br, bg, bb = (int(r * self._BRIGHTNESS), int(g * self._BRIGHTNESS), int(b * self._BRIGHTNESS))
            try:
                for i in range(self._NUM_LEDS):
                    self._stick.set_color(channel=0, index=i, red=br, green=bg, blue=bb)
            except Exception:
                pass

    def _stop_animation(self) -> None:
        self._stop_event.set()
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=2.0)
        self._animation_thread = None

    def _pulse_loop(self, r: int, g: int, b: int, duration: float, speed: float) -> None:
        end_time = time.monotonic() + duration
        while not self._stop_event.is_set() and time.monotonic() < end_time:
            # Fade up
            for i in range(0, 256, 8):
                if self._stop_event.is_set():
                    return
                scale = i / 255.0
                self._set_hw_color(int(r * scale), int(g * scale), int(b * scale))
                time.sleep(speed)
            # Fade down
            for i in range(255, -1, -8):
                if self._stop_event.is_set():
                    return
                scale = i / 255.0
                self._set_hw_color(int(r * scale), int(g * scale), int(b * scale))
                time.sleep(speed)
        # Stay on at full brightness after pulse completes
        self._set_hw_color(r, g, b)

    def _flash_loop(self, r: int, g: int, b: int, count: int, on_time: float, off_time: float) -> None:
        for i in range(count):
            if self._stop_event.is_set():
                return
            self._set_hw_color(r, g, b)
            time.sleep(on_time)
            if self._stop_event.is_set():
                return
            self._set_hw_color(0, 0, 0)
            time.sleep(off_time)
        # Flash done — hold steady at the requested color
        if not self._stop_event.is_set():
            self._set_hw_color(r, g, b)
            self._current_color = (r, g, b)

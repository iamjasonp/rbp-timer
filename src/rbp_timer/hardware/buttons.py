"""GFX HAT capacitive touch button input handling.

Uses direct I2C polling of the CAP1166 sensor input status register
because the cap1xxx library's GPIO interrupt mechanism does not work
reliably on newer Raspberry Pi kernels.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict

# CAP1166 I2C address on the GFX HAT
_CAP1166_ADDR = 0x2C
_REG_MAIN_CONTROL = 0x00
_REG_SENSOR_INPUT_STATUS = 0x03
_REG_INPUT_ENABLE = 0x21
_REG_CALIBRATION_ACTIVATE = 0x26
_REG_CALIBRATION_SENSITIVITY = 0x1F

_HAS_HARDWARE = False
_bus = None

try:
    from smbus import SMBus
    _bus = SMBus(1)
    _HAS_HARDWARE = True
except (ImportError, OSError):
    pass

# Try to use gfxhat touch LEDs (they work fine, just callbacks don't)
try:
    from gfxhat import touch as _touch_leds
except ImportError:
    _touch_leds = None

# Button index constants matching GFX HAT physical labels
UP = 0
DOWN = 1
BACK = 2
MINUS = 3
SELECT = 4
PLUS = 5

BUTTON_NAMES = {UP: "up", DOWN: "down", BACK: "back", MINUS: "minus", SELECT: "select", PLUS: "plus"}

_POLL_INTERVAL = 0.05  # 50ms polling


class Buttons:
    """Handles GFX HAT capacitive touch input via I2C polling."""

    def __init__(self):
        self._handlers: Dict[int, Callable[[], None]] = {}
        self._lock = threading.Lock()
        self._enabled = False
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def register(self, button: int, handler: Callable[[], None]) -> None:
        """Register a callback for a button press."""
        with self._lock:
            self._handlers[button] = handler
        self._update_leds()

    def clear_handlers(self) -> None:
        """Remove all button handlers."""
        with self._lock:
            self._handlers.clear()
        self._update_leds()

    def _update_leds(self) -> None:
        """Turn on LEDs for mapped buttons, off for unmapped ones."""
        if _touch_leds is None or not self._enabled:
            return
        with self._lock:
            mapped = set(self._handlers.keys())
        for btn in range(6):
            _touch_leds.set_led(btn, 1 if btn in mapped else 0)

    def enable(self) -> None:
        """Start listening for button events via I2C polling."""
        if not _HAS_HARDWARE or self._enabled:
            return
        self._enabled = True

        # Initialize CAP1166: enable all 6 inputs, recalibrate
        try:
            _bus.write_byte_data(_CAP1166_ADDR, _REG_INPUT_ENABLE, 0b00111111)
            _bus.write_byte_data(_CAP1166_ADDR, _REG_CALIBRATION_ACTIVATE, 0b00111111)
            _bus.write_byte_data(_CAP1166_ADDR, _REG_CALIBRATION_SENSITIVITY, 0b01000000)
        except OSError:
            pass

        # LEDs will be updated when handlers are registered
        if _touch_leds is not None:
            for btn in range(6):
                _touch_leds.set_led(btn, 0)

        self._stop_event.clear()
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="btn-poll"
        )
        self._poll_thread.start()

    def disable(self) -> None:
        """Stop polling and turn off button LEDs."""
        self._enabled = False
        self._stop_event.set()
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=1.0)
            self._poll_thread = None
        if _touch_leds is not None:
            for btn in range(6):
                _touch_leds.set_led(btn, 0)

    def _poll_loop(self) -> None:
        """Poll the CAP1166 sensor input status register for touches."""
        prev_status = 0
        while not self._stop_event.is_set():
            try:
                status = _bus.read_byte_data(_CAP1166_ADDR, _REG_SENSOR_INPUT_STATUS)
            except OSError:
                time.sleep(_POLL_INTERVAL)
                continue

            # CAP1166 INT flag (bit 0 of MAIN_CONTROL register 0x00):
            # The sensor input status register (0x03) latches and freezes
            # while the INT flag is set. Clear it by writing bit 0 = 0 so
            # the sensor continues reporting new touch events.
            try:
                main = _bus.read_byte_data(_CAP1166_ADDR, _REG_MAIN_CONTROL)
                if main & 0x01:  # INT flag is set
                    _bus.write_byte_data(
                        _CAP1166_ADDR, _REG_MAIN_CONTROL, main & ~0x01  # clear INT flag
                    )
            except OSError:
                pass

            # Detect new presses (bits that went from 0 to 1)
            new_presses = status & ~prev_status
            if new_presses:
                for bit in range(6):
                    if new_presses & (1 << bit):
                        with self._lock:
                            handler = self._handlers.get(bit)
                        if handler:
                            threading.Thread(target=handler, daemon=True).start()

            prev_status = status
            self._stop_event.wait(_POLL_INTERVAL)

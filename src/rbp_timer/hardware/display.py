"""GFX HAT LCD display rendering using Pillow for text/graphics."""

from __future__ import annotations

import threading
from typing import List, Optional, Tuple

try:
    from gfxhat import lcd
except ImportError:
    lcd = None  # Allow development/testing without hardware

from PIL import Image, ImageDraw, ImageFont

WIDTH = 128
HEIGHT = 64


class Display:
    """Renders text and graphics to the GFX HAT 128×64 monochrome LCD.

    Thread-safe: a lock protects the shared image buffer and LCD output
    so that concurrent callers (tick threads, button handlers) cannot
    corrupt a frame mid-render.
    """

    def __init__(self):
        self._image = Image.new("1", (WIDTH, HEIGHT), 0)
        self._draw = ImageDraw.Draw(self._image)
        self._lock = threading.Lock()
        try:
            self._font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
            self._font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
            self._font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
        except (IOError, OSError):
            self._font_large = ImageFont.load_default()
            self._font_medium = ImageFont.load_default()
            self._font_small = ImageFont.load_default()

        # Initialize LCD
        if lcd is not None:
            lcd.clear()
            lcd.show()

    def clear(self) -> None:
        self._draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), fill=0)

    def draw_text(self, x: int, y: int, text: str, font_size: str = "medium") -> None:
        """Draw text at (x, y). font_size: 'small', 'medium', or 'large'."""
        font = {"small": self._font_small, "medium": self._font_medium, "large": self._font_large}.get(
            font_size, self._font_medium
        )
        self._draw.text((x, y), text, fill=1, font=font)

    def draw_centered_text(self, y: int, text: str, font_size: str = "medium") -> None:
        """Draw horizontally centered text at vertical position y."""
        font = {"small": self._font_small, "medium": self._font_medium, "large": self._font_large}.get(
            font_size, self._font_medium
        )
        bbox = self._draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        self._draw.text((x, y), text, fill=1, font=font)

    def draw_timer(self, remaining_seconds: float, label: str = "", sub_label: str = "", progress: float | None = None) -> None:
        """Draw the main timer display with large countdown digits.
        
        progress: 0.0 to 1.0 fraction of elapsed time (None = no bar).
        """
        with self._lock:
            self.clear()
            minutes = int(remaining_seconds) // 60
            seconds = int(remaining_seconds) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            self.draw_centered_text(2, label, "small")
            self.draw_centered_text(16, time_str, "large")
            if sub_label:
                self.draw_centered_text(46, sub_label, "small")

            if progress is not None:
                bar_width = int(WIDTH * max(0.0, min(1.0, progress)))
                if bar_width > 0:
                    self._draw.rectangle((0, HEIGHT - 5, bar_width - 1, HEIGHT - 1), fill=1)

            self.show()

    def draw_menu(self, title: str, items: List[str], selected_index: int) -> None:
        """Draw a menu with a title and selectable items."""
        with self._lock:
            self.clear()
            self.draw_centered_text(0, title, "small")
            self._draw.line((0, 12, WIDTH - 1, 12), fill=1)

            visible_start = max(0, selected_index - 2)
            for i, item_idx in enumerate(range(visible_start, min(len(items), visible_start + 4))):
                y = 16 + i * 12
                prefix = "> " if item_idx == selected_index else "  "
                self.draw_text(2, y, f"{prefix}{items[item_idx]}", "small")

            self.show()

    def draw_setting(self, title: str, value: str, hint: str = "") -> None:
        """Draw a settings adjustment screen."""
        with self._lock:
            self.clear()
            self.draw_centered_text(2, title, "small")
            self.draw_centered_text(20, value, "large")
            if hint:
                self.draw_centered_text(52, hint, "small")
            self.show()

    def draw_message(self, line1: str, line2: str = "") -> None:
        """Draw a simple centered message."""
        with self._lock:
            self.clear()
            self.draw_centered_text(16, line1, "medium")
            if line2:
                self.draw_centered_text(38, line2, "small")
            self.show()

    def begin_frame(self):
        """Acquire the display lock and clear the buffer for atomic frame composition.
        
        Use as a context manager — show() is called automatically on exit:
            with display.begin_frame():
                display.draw_text(...)
                display.draw_centered_text(...)
        """
        self._lock.acquire()
        self.clear()
        return self

    def end_frame(self):
        """Flush the buffer to LCD and release the display lock."""
        self.show()
        self._lock.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end_frame()

    def show(self) -> None:
        """Flush the image buffer to the LCD hardware."""
        if lcd is None:
            return
        for x in range(WIDTH):
            for y in range(HEIGHT):
                lcd.set_pixel(x, y, self._image.getpixel((x, y)))
        lcd.show()

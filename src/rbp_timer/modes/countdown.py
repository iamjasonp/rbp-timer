"""Simple countdown mode — one-shot configurable timer."""

from __future__ import annotations

from typing import Callable, Optional

from rbp_timer.timer import Timer, TimerState


class CountdownMode:
    """A simple one-shot countdown timer with configurable duration."""

    DEFAULT_MINUTES = 10
    MIN_MINUTES = 1
    MAX_MINUTES = 180

    def __init__(self, timer: Timer):
        self.timer = timer
        self._minutes = self.DEFAULT_MINUTES

        self.on_finished: Optional[Callable[[], None]] = None

    @property
    def minutes(self) -> int:
        return self._minutes

    def set_minutes(self, minutes: int) -> None:
        """Set the countdown duration in minutes (clamped to valid range)."""
        self._minutes = max(self.MIN_MINUTES, min(self.MAX_MINUTES, minutes))

    def adjust_minutes(self, delta: int) -> None:
        """Adjust minutes by a delta (positive or negative)."""
        self.set_minutes(self._minutes + delta)

    def start(self) -> None:
        """Start the countdown."""
        self.timer.set_duration(self._minutes * 60)
        self.timer.start()

    def stop(self) -> None:
        """Stop and reset."""
        self.timer.stop()

    def _on_timer_done(self) -> None:
        if self.on_finished:
            self.on_finished()

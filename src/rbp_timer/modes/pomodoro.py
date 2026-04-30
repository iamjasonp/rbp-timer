"""Pomodoro mode — 25/5/15 minute work/break cycles."""

from __future__ import annotations

import enum
from typing import Callable, Optional

from rbp_timer.timer import Timer, TimerState


class PomodoroPhase(enum.Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroMode:
    """Manages Pomodoro timer cycles with auto-advance."""

    WORK_MINUTES = 25
    SHORT_BREAK_MINUTES = 5
    LONG_BREAK_MINUTES = 15
    CYCLES_BEFORE_LONG_BREAK = 4

    def __init__(self, timer: Timer):
        self.timer = timer
        self._phase = PomodoroPhase.WORK
        self._completed_cycles = 0

        # Callbacks
        self.on_phase_change: Optional[Callable[[PomodoroPhase, int], None]] = None

    @property
    def phase(self) -> PomodoroPhase:
        return self._phase

    @property
    def completed_cycles(self) -> int:
        return self._completed_cycles

    def start(self) -> None:
        """Start the first work session."""
        self._phase = PomodoroPhase.WORK
        self._completed_cycles = 0
        self._apply_phase()
        self.timer.start()

    def skip(self) -> None:
        """Skip the current phase and advance to the next."""
        self.timer.stop()
        self._advance_phase()
        self._apply_phase()
        self.timer.start()

    def stop(self) -> None:
        """Stop and fully reset the Pomodoro."""
        self.timer.stop()
        self._phase = PomodoroPhase.WORK
        self._completed_cycles = 0

    def _apply_phase(self) -> None:
        """Set the timer duration based on the current phase."""
        durations = {
            PomodoroPhase.WORK: self.WORK_MINUTES * 60,
            PomodoroPhase.SHORT_BREAK: self.SHORT_BREAK_MINUTES * 60,
            PomodoroPhase.LONG_BREAK: self.LONG_BREAK_MINUTES * 60,
        }
        self.timer.set_duration(durations[self._phase])
        if self.on_phase_change:
            self.on_phase_change(self._phase, self._completed_cycles)

    def _advance_phase(self) -> None:
        """Move to the next phase in the cycle."""
        if self._phase == PomodoroPhase.WORK:
            self._completed_cycles += 1
            if self._completed_cycles % self.CYCLES_BEFORE_LONG_BREAK == 0:
                self._phase = PomodoroPhase.LONG_BREAK
            else:
                self._phase = PomodoroPhase.SHORT_BREAK
        else:
            self._phase = PomodoroPhase.WORK

    def _on_timer_done(self) -> None:
        """Called when the timer finishes — auto-advance to next phase."""
        self._advance_phase()
        self._apply_phase()
        self.timer.start()

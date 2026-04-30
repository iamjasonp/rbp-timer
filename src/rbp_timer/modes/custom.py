"""Custom intervals mode — user-defined work/break durations with cycles."""

from __future__ import annotations

import enum
import json
import os
from typing import Callable, Optional

from rbp_timer.timer import Timer, TimerState


CONFIG_PATH = os.path.expanduser("~/.config/rbp-timer/custom.json")


class CustomPhase(enum.Enum):
    WORK = "work"
    BREAK = "break"


class CustomMode:
    """Custom intervals with configurable work/break durations and cycle count."""

    DEFAULT_WORK_MINUTES = 25
    DEFAULT_BREAK_MINUTES = 5
    DEFAULT_CYCLES = 4
    MIN_MINUTES = 1
    MAX_MINUTES = 180
    MIN_CYCLES = 1
    MAX_CYCLES = 20

    def __init__(self, timer: Timer):
        self.timer = timer
        self._work_minutes = self.DEFAULT_WORK_MINUTES
        self._break_minutes = self.DEFAULT_BREAK_MINUTES
        self._total_cycles = self.DEFAULT_CYCLES
        self._current_cycle = 0
        self._phase = CustomPhase.WORK

        self.on_phase_change: Optional[Callable[[CustomPhase, int, int], None]] = None
        self.on_all_done: Optional[Callable[[], None]] = None

        self._load_config()

    @property
    def work_minutes(self) -> int:
        return self._work_minutes

    @property
    def break_minutes(self) -> int:
        return self._break_minutes

    @property
    def total_cycles(self) -> int:
        return self._total_cycles

    @property
    def current_cycle(self) -> int:
        return self._current_cycle

    @property
    def phase(self) -> CustomPhase:
        return self._phase

    def set_work_minutes(self, minutes: int) -> None:
        self._work_minutes = max(self.MIN_MINUTES, min(self.MAX_MINUTES, minutes))
        self._save_config()

    def set_break_minutes(self, minutes: int) -> None:
        self._break_minutes = max(self.MIN_MINUTES, min(self.MAX_MINUTES, minutes))
        self._save_config()

    def set_total_cycles(self, cycles: int) -> None:
        self._total_cycles = max(self.MIN_CYCLES, min(self.MAX_CYCLES, cycles))
        self._save_config()

    def start(self) -> None:
        """Start the custom interval session."""
        self._current_cycle = 0
        self._phase = CustomPhase.WORK
        self._apply_phase()
        self.timer.start()

    def skip(self) -> None:
        """Skip the current phase and advance to the next."""
        self.timer.stop()
        if self._phase == CustomPhase.WORK:
            self._current_cycle += 1
            if self._current_cycle >= self._total_cycles:
                if self.on_all_done:
                    self.on_all_done()
                return
            self._phase = CustomPhase.BREAK
        else:
            self._phase = CustomPhase.WORK
        self._apply_phase()
        self.timer.start()

    def stop(self) -> None:
        """Stop and reset."""
        self.timer.stop()
        self._current_cycle = 0
        self._phase = CustomPhase.WORK

    def _apply_phase(self) -> None:
        if self._phase == CustomPhase.WORK:
            self.timer.set_duration(self._work_minutes * 60)
        else:
            self.timer.set_duration(self._break_minutes * 60)
        if self.on_phase_change:
            self.on_phase_change(self._phase, self._current_cycle, self._total_cycles)

    def _on_timer_done(self) -> None:
        if self._phase == CustomPhase.WORK:
            self._current_cycle += 1
            if self._current_cycle >= self._total_cycles:
                if self.on_all_done:
                    self.on_all_done()
                return
            self._phase = CustomPhase.BREAK
        else:
            self._phase = CustomPhase.WORK

        self._apply_phase()
        self.timer.start()

    def _load_config(self) -> None:
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            self._work_minutes = max(self.MIN_MINUTES, min(self.MAX_MINUTES,
                int(data.get("work_minutes", self.DEFAULT_WORK_MINUTES))))
            self._break_minutes = max(self.MIN_MINUTES, min(self.MAX_MINUTES,
                int(data.get("break_minutes", self.DEFAULT_BREAK_MINUTES))))
            self._total_cycles = max(self.MIN_CYCLES, min(self.MAX_CYCLES,
                int(data.get("total_cycles", self.DEFAULT_CYCLES))))
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    def _save_config(self) -> None:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        data = {
            "work_minutes": self._work_minutes,
            "break_minutes": self._break_minutes,
            "total_cycles": self._total_cycles,
        }
        tmp_path = CONFIG_PATH + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, CONFIG_PATH)
        except OSError:
            pass

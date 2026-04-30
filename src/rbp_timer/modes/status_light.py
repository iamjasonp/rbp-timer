"""Status Light mode — count-up timer with availability states."""

from __future__ import annotations

import enum
import time
from typing import Callable, Dict, Optional


class StatusLightState(enum.Enum):
    AVAILABLE = "available"
    AWAY = "away"
    BUSY = "busy"


class StatusLightMode:
    """Tracks elapsed time across three availability states."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._state = StatusLightState.AVAILABLE
        self._state_start: float = 0.0
        self._total_start: float = 0.0
        self._accumulated: Dict[StatusLightState, float] = {
            StatusLightState.AVAILABLE: 0.0,
            StatusLightState.AWAY: 0.0,
            StatusLightState.BUSY: 0.0,
        }
        self._running = False

        self.on_state_change: Optional[Callable[[StatusLightState], None]] = None

    @property
    def state(self) -> StatusLightState:
        return self._state

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the status light in Available state."""
        now = self._clock()
        self._state = StatusLightState.AVAILABLE
        self._state_start = now
        self._total_start = now
        self._accumulated = {s: 0.0 for s in StatusLightState}
        self._running = True

    def set_state(self, new_state: StatusLightState) -> None:
        """Switch to a new state. No-op if already in that state."""
        if not self._running or new_state == self._state:
            return
        now = self._clock()
        self._accumulated[self._state] += now - self._state_start
        self._state = new_state
        self._state_start = now
        if self.on_state_change:
            self.on_state_change(new_state)

    def current_state_elapsed(self) -> float:
        """Seconds elapsed in the current state."""
        if not self._running:
            return 0.0
        return self._clock() - self._state_start

    def total_elapsed(self) -> float:
        """Total seconds elapsed since start."""
        if not self._running:
            return 0.0
        return self._clock() - self._total_start

    def get_summary(self) -> Dict[str, float]:
        """Per-state totals (including current running state) and grand total."""
        result = {}
        now = self._clock() if self._running else self._state_start
        for s in StatusLightState:
            total = self._accumulated[s]
            if self._running and s == self._state:
                total += now - self._state_start
            result[s.value] = total
        result["total"] = sum(result[s.value] for s in StatusLightState)
        return result

    def reset(self) -> None:
        """Stop and zero everything."""
        self._running = False
        self._accumulated = {s: 0.0 for s in StatusLightState}
        self._state = StatusLightState.AVAILABLE
        self._state_start = 0.0
        self._total_start = 0.0

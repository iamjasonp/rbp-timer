"""Core timer engine — pure countdown logic with no hardware dependencies."""

from __future__ import annotations

import enum
import time
import threading
from typing import Callable, Optional


class TimerState(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"


class Timer:
    """A general-purpose countdown timer with start/pause/resume/stop/reset.

    Thread-safe: all public methods acquire _lock before mutating state.
    The on_done callback is invoked *after* the timer thread exits, so it is
    safe for callers to call start() again from on_done without re-entrancy.
    """

    def __init__(self, tick_interval: float = 0.25):
        self._duration: float = 0.0
        self._remaining: float = 0.0
        self._state = TimerState.IDLE
        self._tick_interval = tick_interval
        self._lock = threading.Lock()

        self._last_tick_time: float = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._generation = 0  # incremented on each start to detect stale threads

        # Callbacks
        self.on_tick: Optional[Callable[[float], None]] = None
        self.on_state_change: Optional[Callable[[TimerState], None]] = None
        self.on_done: Optional[Callable[[], None]] = None

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def remaining(self) -> float:
        return max(0.0, self._remaining)

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def elapsed(self) -> float:
        return self._duration - self._remaining

    def adjust_remaining(self, delta: float) -> None:
        """Add or subtract time from the running/paused timer."""
        with self._lock:
            if self._state in (TimerState.RUNNING, TimerState.PAUSED):
                self._remaining = max(0.0, self._remaining + delta)
                self._duration = max(0.0, self._duration + delta)

    def _set_state(self, new_state: TimerState) -> None:
        if new_state != self._state:
            self._state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)

    def set_duration(self, seconds: float) -> None:
        """Set the countdown duration. Only allowed when IDLE or DONE."""
        with self._lock:
            if self._state not in (TimerState.IDLE, TimerState.DONE):
                return
            self._duration = seconds
            self._remaining = seconds

    def start(self) -> None:
        """Start or resume the timer."""
        with self._lock:
            if self._state == TimerState.IDLE or self._state == TimerState.DONE:
                self._remaining = self._duration
                self._start_thread_locked()
            elif self._state == TimerState.PAUSED:
                self._start_thread_locked()

    def pause(self) -> None:
        """Pause a running timer."""
        with self._lock:
            if self._state == TimerState.RUNNING:
                self._stop_event.set()
                thread = self._thread
        # Join outside lock to avoid deadlock
        if self._state != TimerState.PAUSED and thread:
            thread.join(timeout=2.0)
        with self._lock:
            if self._state == TimerState.RUNNING:
                self._set_state(TimerState.PAUSED)

    def resume(self) -> None:
        """Resume a paused timer."""
        with self._lock:
            if self._state == TimerState.PAUSED:
                self._start_thread_locked()

    def stop(self) -> None:
        """Stop and reset the timer."""
        with self._lock:
            self._stop_event.set()
            self._generation += 1
            thread = self._thread
        if thread:
            thread.join(timeout=2.0)
        with self._lock:
            self._remaining = self._duration
            self._set_state(TimerState.IDLE)

    def reset(self) -> None:
        """Alias for stop — resets the timer to its initial duration."""
        self.stop()

    def _start_thread_locked(self) -> None:
        """Must be called with _lock held."""
        # Stop any existing thread
        self._stop_event.set()
        old_thread = self._thread
        # Only join if we're not being called from that same thread
        if old_thread and old_thread.is_alive() and old_thread is not threading.current_thread():
            self._lock.release()
            old_thread.join(timeout=2.0)
            self._lock.acquire()

        self._generation += 1
        self._stop_event.clear()
        self._last_tick_time = time.monotonic()
        self._set_state(TimerState.RUNNING)
        gen = self._generation
        self._thread = threading.Thread(target=self._run, args=(gen,), daemon=True)
        self._thread.start()

    def _run(self, generation: int) -> None:
        done_callback = None
        while not self._stop_event.is_set():
            now = time.monotonic()
            dt = now - self._last_tick_time
            self._last_tick_time = now
            self._remaining -= dt

            if self._remaining <= 0:
                self._remaining = 0.0
                if self.on_tick:
                    self.on_tick(0.0)
                with self._lock:
                    # Check generation — if it changed, we've been superseded
                    if self._generation != generation:
                        return
                    self._set_state(TimerState.DONE)
                    done_callback = self.on_done
                # Fire on_done *outside* the lock and *after* the thread's loop ends
                if done_callback:
                    done_callback()
                return

            if self.on_tick:
                self.on_tick(self._remaining)

            self._stop_event.wait(self._tick_interval)

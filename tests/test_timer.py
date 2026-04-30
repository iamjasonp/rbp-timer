"""Tests for the core timer engine."""

import threading
import time
import pytest
from rbp_timer.timer import Timer, TimerState


class TestTimerStates:
    def test_initial_state_is_idle(self):
        t = Timer()
        assert t.state == TimerState.IDLE

    def test_set_duration(self):
        t = Timer()
        t.set_duration(300)
        assert t.duration == 300
        assert t.remaining == 300

    def test_start_transitions_to_running(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        assert t.state == TimerState.RUNNING
        t.stop()

    def test_pause_transitions_to_paused(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        t.pause()
        assert t.state == TimerState.PAUSED

    def test_resume_transitions_to_running(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        t.pause()
        t.resume()
        assert t.state == TimerState.RUNNING
        t.stop()

    def test_stop_transitions_to_idle(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        t.stop()
        assert t.state == TimerState.IDLE

    def test_stop_resets_remaining(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        time.sleep(0.1)
        t.stop()
        assert t.remaining == 10

    def test_remaining_decreases_while_running(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        time.sleep(0.5)
        assert t.remaining < 10
        t.stop()

    def test_remaining_holds_while_paused(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        time.sleep(0.3)
        t.pause()
        paused_remaining = t.remaining
        time.sleep(0.3)
        assert t.remaining == paused_remaining

    def test_set_duration_ignored_while_running(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        t.set_duration(99)
        assert t.duration == 10
        t.stop()


class TestTimerCallbacks:
    def test_on_tick_called(self):
        ticks = []
        t = Timer(tick_interval=0.05)
        t.on_tick = lambda r: ticks.append(r)
        t.set_duration(5)
        t.start()
        time.sleep(0.3)
        t.stop()
        assert len(ticks) > 0

    def test_on_state_change_called(self):
        states = []
        t = Timer()
        t.on_state_change = lambda s: states.append(s)
        t.set_duration(5)
        t.start()
        t.pause()
        t.resume()
        t.stop()
        assert TimerState.RUNNING in states
        assert TimerState.PAUSED in states
        assert TimerState.IDLE in states

    def test_on_done_called(self):
        done_event = threading.Event()
        t = Timer(tick_interval=0.01)
        t.on_done = lambda: done_event.set()
        t.set_duration(0.1)
        t.start()
        done_event.wait(timeout=2.0)
        assert done_event.is_set()
        assert t.state == TimerState.DONE

    def test_elapsed_property(self):
        t = Timer()
        t.set_duration(10)
        t.start()
        time.sleep(0.3)
        elapsed = t.elapsed
        t.stop()
        assert elapsed > 0
        assert elapsed < 10

"""Tests for timer modes (Pomodoro, Countdown, Custom)."""

import threading
import time
import pytest
from unittest.mock import MagicMock

from rbp_timer.timer import Timer, TimerState
from rbp_timer.modes.pomodoro import PomodoroMode, PomodoroPhase
from rbp_timer.modes.countdown import CountdownMode
from rbp_timer.modes.custom import CustomMode, CustomPhase, CONFIG_PATH


class TestPomodoroMode:
    def test_initial_phase_is_work(self):
        t = Timer()
        p = PomodoroMode(t)
        assert p.phase == PomodoroPhase.WORK

    def test_start_sets_work_duration(self):
        t = Timer()
        p = PomodoroMode(t)
        p.start()
        assert t.duration == 25 * 60
        assert t.state == TimerState.RUNNING
        t.stop()

    def test_stop_resets_cycle(self):
        t = Timer()
        p = PomodoroMode(t)
        p.start()
        p.stop()
        assert p.phase == PomodoroPhase.WORK
        assert p.completed_cycles == 0

    def test_phase_advances_work_to_short_break(self):
        t = Timer(tick_interval=0.01)
        p = PomodoroMode(t)
        phase_changes = []
        p.on_phase_change = lambda phase, cycle: phase_changes.append((phase, cycle))

        # Use a very short duration to test phase transition
        p.WORK_MINUTES = 0.001  # ~0.06 seconds
        p.SHORT_BREAK_MINUTES = 0.001
        # Wire on_done manually since App normally dispatches this
        t.on_done = p._on_timer_done
        p.start()
        time.sleep(0.5)
        t.stop()

        # Should have advanced past work phase
        assert len(phase_changes) > 1

    def test_long_break_after_4_cycles(self):
        t = Timer()
        p = PomodoroMode(t)
        # Manually advance phases to test cycle counting
        p._phase = PomodoroPhase.WORK
        p._completed_cycles = 3
        p._advance_phase()
        assert p.phase == PomodoroPhase.LONG_BREAK
        assert p.completed_cycles == 4

    def test_short_break_before_4_cycles(self):
        t = Timer()
        p = PomodoroMode(t)
        p._phase = PomodoroPhase.WORK
        p._completed_cycles = 0
        p._advance_phase()
        assert p.phase == PomodoroPhase.SHORT_BREAK
        assert p.completed_cycles == 1

    def test_break_advances_to_work(self):
        t = Timer()
        p = PomodoroMode(t)
        p._phase = PomodoroPhase.SHORT_BREAK
        p._advance_phase()
        assert p.phase == PomodoroPhase.WORK


class TestCountdownMode:
    def test_default_minutes(self):
        t = Timer()
        c = CountdownMode(t)
        assert c.minutes == 10

    def test_set_minutes_clamped(self):
        t = Timer()
        c = CountdownMode(t)
        c.set_minutes(0)
        assert c.minutes == 1
        c.set_minutes(999)
        assert c.minutes == 180

    def test_adjust_minutes(self):
        t = Timer()
        c = CountdownMode(t)
        c.set_minutes(10)
        c.adjust_minutes(5)
        assert c.minutes == 15
        c.adjust_minutes(-20)
        assert c.minutes == 1

    def test_start_sets_duration(self):
        t = Timer()
        c = CountdownMode(t)
        c.set_minutes(5)
        c.start()
        assert t.duration == 300
        assert t.state == TimerState.RUNNING
        t.stop()

    def test_on_finished_callback(self):
        t = Timer(tick_interval=0.01)
        c = CountdownMode(t)
        finished = threading.Event()
        c.on_finished = lambda: finished.set()
        c.set_minutes(1)
        # Override duration to finish quickly
        t.set_duration = Timer.set_duration.__get__(t)
        c.start()
        t.stop()
        t.set_duration(0.05)
        t.on_done = c._on_timer_done
        t.start()
        finished.wait(timeout=2.0)
        assert finished.is_set()


class TestCustomMode:
    def setup_method(self):
        """Remove any persisted config to ensure test isolation."""
        import os
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)

    def test_defaults(self):
        t = Timer()
        c = CustomMode(t)
        assert c.work_minutes == 25
        assert c.break_minutes == 5
        assert c.total_cycles == 4

    def test_set_work_minutes_clamped(self):
        t = Timer()
        c = CustomMode(t)
        c.set_work_minutes(0)
        assert c.work_minutes == 1
        c.set_work_minutes(999)
        assert c.work_minutes == 180

    def test_set_break_minutes_clamped(self):
        t = Timer()
        c = CustomMode(t)
        c.set_break_minutes(0)
        assert c.break_minutes == 1

    def test_set_cycles_clamped(self):
        t = Timer()
        c = CustomMode(t)
        c.set_total_cycles(0)
        assert c.total_cycles == 1
        c.set_total_cycles(100)
        assert c.total_cycles == 20

    def test_start_begins_work_phase(self):
        t = Timer()
        c = CustomMode(t)
        c.start()
        assert c.phase == CustomPhase.WORK
        assert t.state == TimerState.RUNNING
        t.stop()

    def test_stop_resets(self):
        t = Timer()
        c = CustomMode(t)
        c.start()
        c.stop()
        assert c.current_cycle == 0
        assert c.phase == CustomPhase.WORK

    def test_phase_advance_work_to_break(self):
        t = Timer()
        c = CustomMode(t)
        c._phase = CustomPhase.WORK
        c._current_cycle = 0
        c._total_cycles = 4
        c._on_timer_done()
        assert c.phase == CustomPhase.BREAK
        assert c.current_cycle == 1

    def test_phase_advance_break_to_work(self):
        t = Timer()
        c = CustomMode(t)
        c._phase = CustomPhase.BREAK
        c._on_timer_done()
        assert c.phase == CustomPhase.WORK

    def test_all_done_callback(self):
        t = Timer()
        c = CustomMode(t)
        done = MagicMock()
        c.on_all_done = done
        c._total_cycles = 1
        c._phase = CustomPhase.WORK
        c._current_cycle = 0
        c._on_timer_done()
        done.assert_called_once()

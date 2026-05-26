"""Tests for StatusLightMode — count-up timer with availability states."""

import pytest
from rbp_timer.modes.status_light import StatusLightMode, StatusLightState


class FakeClock:
    """Deterministic clock for testing elapsed time logic."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class TestStatusLightStart:
    def test_initial_state_before_start(self):
        mode = StatusLightMode()
        assert mode.state == StatusLightState.AVAILABLE
        assert mode.running is False

    def test_start_sets_available_and_running(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        assert mode.state == StatusLightState.AVAILABLE
        assert mode.running is True

    def test_elapsed_zero_before_start(self):
        mode = StatusLightMode()
        assert mode.current_state_elapsed() == 0.0
        assert mode.total_elapsed() == 0.0


class TestStatusLightStateTransitions:
    def test_switch_to_different_state(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        mode.set_state(StatusLightState.BUSY)
        assert mode.state == StatusLightState.BUSY

    def test_same_state_is_noop(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        mode.set_state(StatusLightState.AVAILABLE)
        # Should still show 10s elapsed, not reset to 0
        assert mode.current_state_elapsed() == 10.0

    def test_set_state_before_start_is_noop(self):
        mode = StatusLightMode()
        mode.set_state(StatusLightState.BUSY)
        assert mode.state == StatusLightState.AVAILABLE
        assert mode.running is False

    def test_state_change_callback_fires(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        received = []
        mode.on_state_change = lambda s: received.append(s)
        mode.start()
        mode.set_state(StatusLightState.AWAY)
        assert received == [StatusLightState.AWAY]

    def test_same_state_callback_does_not_fire(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        received = []
        mode.on_state_change = lambda s: received.append(s)
        mode.start()
        mode.set_state(StatusLightState.AVAILABLE)
        assert received == []


class TestStatusLightElapsed:
    def test_current_state_elapsed_tracks_time(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(30)
        assert mode.current_state_elapsed() == 30.0

    def test_current_state_elapsed_resets_on_switch(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(30)
        mode.set_state(StatusLightState.BUSY)
        clock.advance(5)
        assert mode.current_state_elapsed() == 5.0

    def test_total_elapsed_spans_all_states(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        mode.set_state(StatusLightState.AWAY)
        clock.advance(20)
        mode.set_state(StatusLightState.BUSY)
        clock.advance(5)
        assert mode.total_elapsed() == 35.0


class TestStatusLightSummary:
    def test_summary_includes_current_state(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        summary = mode.get_summary()
        assert summary["available"] == 10.0
        assert summary["away"] == 0.0
        assert summary["busy"] == 0.0
        assert summary["total"] == 10.0

    def test_summary_after_transitions(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        mode.set_state(StatusLightState.AWAY)
        clock.advance(20)
        mode.set_state(StatusLightState.BUSY)
        clock.advance(5)
        summary = mode.get_summary()
        assert summary["available"] == 10.0
        assert summary["away"] == 20.0
        assert summary["busy"] == 5.0
        assert summary["total"] == 35.0

    def test_summary_accumulates_across_revisits(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(10)
        mode.set_state(StatusLightState.BUSY)
        clock.advance(5)
        mode.set_state(StatusLightState.AVAILABLE)
        clock.advance(15)
        summary = mode.get_summary()
        assert summary["available"] == 25.0  # 10 + 15
        assert summary["busy"] == 5.0
        assert summary["total"] == 30.0


class TestStatusLightReset:
    def test_reset_zeroes_everything(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(60)
        mode.set_state(StatusLightState.BUSY)
        clock.advance(30)
        mode.reset()
        assert mode.running is False
        assert mode.state == StatusLightState.AVAILABLE
        assert mode.current_state_elapsed() == 0.0
        assert mode.total_elapsed() == 0.0
        summary = mode.get_summary()
        assert summary["total"] == 0.0

    def test_restart_after_reset(self):
        clock = FakeClock()
        mode = StatusLightMode(clock=clock)
        mode.start()
        clock.advance(100)
        mode.reset()
        clock.advance(50)
        mode.start()
        clock.advance(10)
        assert mode.current_state_elapsed() == 10.0
        assert mode.total_elapsed() == 10.0

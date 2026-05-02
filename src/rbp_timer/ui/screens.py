"""Screen rendering helpers — bridge between UI state and display hardware."""

from __future__ import annotations

from rbp_timer.hardware.display import Display
from rbp_timer.modes.pomodoro import PomodoroPhase
from rbp_timer.modes.custom import CustomPhase
from rbp_timer.modes.status_light import StatusLightState
from rbp_timer.timer import TimerState


def render_main_menu(display: Display, items: list[str], selected: int) -> None:
    display.draw_menu("Jasondoro Timer", items, selected)


def render_pomodoro(display: Display, remaining: float, phase: PomodoroPhase, cycle: int, duration: float = 0) -> None:
    phase_labels = {
        PomodoroPhase.WORK: "WORK",
        PomodoroPhase.SHORT_BREAK: "SHORT BREAK",
        PomodoroPhase.LONG_BREAK: "LONG BREAK",
    }
    label = phase_labels.get(phase, "")
    sub = f"Cycle {cycle + 1}"
    progress = (duration - remaining) / duration if duration > 0 else None
    display.draw_timer(remaining, label=label, sub_label=sub, progress=progress)


def render_countdown(display: Display, remaining: float, timer_state: TimerState) -> None:
    state_label = ""
    if timer_state == TimerState.PAUSED:
        state_label = "PAUSED"
    elif timer_state == TimerState.DONE:
        state_label = "DONE!"
    display.draw_timer(remaining, label="COUNTDOWN", sub_label=state_label)


def render_custom(display: Display, remaining: float, phase: CustomPhase, cycle: int, total: int, duration: float = 0) -> None:
    phase_label = "WORK" if phase == CustomPhase.WORK else "BREAK"
    sub = f"Cycle {cycle + 1}/{total}"
    progress = (duration - remaining) / duration if duration > 0 else None
    display.draw_timer(remaining, label=phase_label, sub_label=sub, progress=progress)


def render_countdown_settings(display: Display, minutes: int) -> None:
    display.draw_setting("Set Duration", f"{minutes} min", "UP/DOWN to adjust")


def render_custom_settings(display: Display, field: str, value: int) -> None:
    labels = {
        "work": "Work Minutes",
        "break": "Break Minutes",
        "cycles": "Cycles",
    }
    display.draw_setting(labels.get(field, field), str(value), "UP/DOWN to adjust")


def _format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as MM:SS or H:MM:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def render_status_light(display: Display, state: StatusLightState, state_elapsed: float, total_elapsed: float) -> None:
    state_labels = {
        StatusLightState.AVAILABLE: "AVAILABLE",
        StatusLightState.AWAY: "AWAY",
        StatusLightState.BUSY: "BUSY",
    }
    label = state_labels.get(state, "")
    time_str = _format_elapsed(state_elapsed)
    with display.begin_frame():
        display.draw_centered_text(2, label, "small")
        display.draw_centered_text(16, time_str, "large")


def render_status_summary(display: Display, summary: dict) -> None:
    avail = _format_elapsed(summary.get("available", 0))
    away = _format_elapsed(summary.get("away", 0))
    busy = _format_elapsed(summary.get("busy", 0))
    total = _format_elapsed(summary.get("total", 0))
    with display.begin_frame():
        display.draw_centered_text(0, "TIMER PAUSED", "small")
        display.draw_text(2, 14, f"Avail: {avail}", "small")
        display.draw_text(2, 26, f"Away:  {away}", "small")
        display.draw_text(2, 38, f"Busy:  {busy}", "small")
        display.draw_text(2, 50, f"Total: {total}", "small")

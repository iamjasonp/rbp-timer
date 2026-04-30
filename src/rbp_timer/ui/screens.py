"""Screen rendering helpers — bridge between UI state and display hardware."""

from __future__ import annotations

from rbp_timer.hardware.display import Display
from rbp_timer.modes.pomodoro import PomodoroPhase
from rbp_timer.modes.custom import CustomPhase
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

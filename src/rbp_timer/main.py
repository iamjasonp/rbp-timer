"""Main application — wires hardware, UI, and timer together."""

from __future__ import annotations

import signal
import sys
import threading
from typing import Optional

from rbp_timer.timer import Timer, TimerState
from rbp_timer.modes.pomodoro import PomodoroMode, PomodoroPhase
from rbp_timer.modes.countdown import CountdownMode
from rbp_timer.modes.custom import CustomMode, CustomPhase
from rbp_timer.hardware.display import Display
from rbp_timer.hardware.backlight import Backlight
from rbp_timer.hardware.buttons import Buttons, UP, DOWN, BACK, MINUS, SELECT, PLUS
from rbp_timer.hardware.blinkstick_ctrl import BlinkStickController
from rbp_timer.ui.menu import Menu, MenuState
from rbp_timer.ui import screens


class App:
    """Main application controller."""

    def __init__(self):
        self.timer = Timer()
        self.display = Display()
        self.backlight = Backlight()
        self.buttons = Buttons()
        self.blinkstick = BlinkStickController()
        self.menu = Menu()

        # Modes
        self.pomodoro = PomodoroMode(self.timer)
        self.countdown = CountdownMode(self.timer)
        self.custom = CustomMode(self.timer)

        self._active_mode: Optional[str] = None
        self._shutdown_event = threading.Event()

        # Custom settings navigation
        self._custom_setting_fields = ["work", "break", "cycles"]
        self._custom_setting_index = 0

        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        # Menu callbacks
        self.menu.on_mode_selected = self._on_mode_selected
        self.menu.on_back_to_menu = self._show_main_menu
        self.menu.on_redraw = self._draw_menu

        # Use a single stable on_done that dispatches based on active mode
        self.timer.on_tick = self._on_tick
        self.timer.on_state_change = self._on_timer_state_change
        self.timer.on_done = self._on_timer_done

    def run(self) -> None:
        """Start the application."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self.buttons.enable()
        self._show_main_menu()

        # Block until shutdown
        self._shutdown_event.wait()
        self._cleanup()

    def _signal_handler(self, signum, frame) -> None:
        self._shutdown_event.set()

    def _cleanup(self) -> None:
        self.timer.stop()
        self.buttons.disable()
        self.backlight.off()
        self.blinkstick.cleanup()
        self.display.clear()
        self.display.show()

    # ── Menu ──

    def _show_main_menu(self) -> None:
        self._active_mode = None
        self.timer.stop()
        self.backlight.set_state("menu")
        self.blinkstick.off()
        self.menu._state = MenuState.MAIN
        self._draw_menu()
        self._bind_menu_buttons()

    def _draw_menu(self) -> None:
        screens.render_main_menu(self.display, Menu.MAIN_ITEMS, self.menu.selected_index)

    def _bind_menu_buttons(self) -> None:
        self.buttons.clear_handlers()
        self.buttons.register(UP, self.menu.navigate_up)
        self.buttons.register(DOWN, self.menu.navigate_down)
        self.buttons.register(SELECT, self.menu.select)

    # ── Mode Selection ──

    def _on_mode_selected(self, mode: str) -> None:
        self._active_mode = mode
        if mode == "pomodoro":
            self._start_pomodoro()
        elif mode == "countdown":
            self._show_countdown_settings()
        elif mode == "custom":
            self._show_custom_settings()

    # ── Pomodoro ──

    def _start_pomodoro(self) -> None:
        self.pomodoro.on_phase_change = self._on_pomodoro_phase
        self.pomodoro.start()
        # Initial start: set steady color (no flash)
        phase = self.pomodoro.phase
        if phase == PomodoroPhase.WORK:
            self.backlight.set_state("work")
        else:
            self.backlight.set_state("break")
        r, g, b = self.backlight.current_color
        self.blinkstick.set_color(r, g, b)
        self._bind_timer_buttons()
        self.buttons.register(PLUS, self._skip_pomodoro_phase)

    def _skip_pomodoro_phase(self) -> None:
        self.pomodoro.skip()
        self._update_pomodoro_visuals()
        self._bind_timer_buttons()
        self.buttons.register(PLUS, self._skip_pomodoro_phase)

    def _on_pomodoro_phase(self, phase: PomodoroPhase, cycle: int) -> None:
        self._update_pomodoro_visuals()

    def _update_pomodoro_visuals(self) -> None:
        phase = self.pomodoro.phase
        if phase == PomodoroPhase.WORK:
            self.backlight.set_state("work")
        else:
            self.backlight.set_state("break")
        r, g, b = self.backlight.current_color
        # Flash to signal transition, then hold steady
        self.blinkstick.flash(r, g, b, count=3)

    # ── Countdown ──

    def _show_countdown_settings(self) -> None:
        self.buttons.clear_handlers()
        screens.render_countdown_settings(self.display, self.countdown.minutes)

        def up():
            self.countdown.adjust_minutes(1)
            screens.render_countdown_settings(self.display, self.countdown.minutes)

        def down():
            self.countdown.adjust_minutes(-1)
            screens.render_countdown_settings(self.display, self.countdown.minutes)

        def confirm():
            self._start_countdown()

        self.buttons.register(UP, up)
        self.buttons.register(DOWN, down)
        self.buttons.register(SELECT, confirm)
        self.buttons.register(BACK, lambda: self.menu.back())

    def _start_countdown(self) -> None:
        self.countdown.start()
        self.backlight.set_state("work")
        r, g, b = self.backlight.current_color
        self.blinkstick.set_color(r, g, b)
        self._bind_timer_buttons()
        self.buttons.register(PLUS, lambda: self.timer.adjust_remaining(60))
        self.buttons.register(MINUS, lambda: self.timer.adjust_remaining(-60))

    def _on_countdown_done(self) -> None:
        self.backlight.set_state("done")
        self.blinkstick.flash(0, 128, 0, count=5)
        self.display.draw_message("Time's Up!", "Press any button")
        self.buttons.clear_handlers()
        for btn in range(6):
            self.buttons.register(btn, self._show_main_menu)

    # ── Custom ──

    def _show_custom_settings(self) -> None:
        self._custom_setting_index = 0
        self._draw_custom_setting()
        self._bind_custom_settings_buttons()

    def _draw_custom_setting(self) -> None:
        field = self._custom_setting_fields[self._custom_setting_index]
        values = {
            "work": self.custom.work_minutes,
            "break": self.custom.break_minutes,
            "cycles": self.custom.total_cycles,
        }
        screens.render_custom_settings(self.display, field, values[field])

    def _bind_custom_settings_buttons(self) -> None:
        self.buttons.clear_handlers()

        def up():
            field = self._custom_setting_fields[self._custom_setting_index]
            if field == "work":
                self.custom.set_work_minutes(self.custom.work_minutes + 1)
            elif field == "break":
                self.custom.set_break_minutes(self.custom.break_minutes + 1)
            elif field == "cycles":
                self.custom.set_total_cycles(self.custom.total_cycles + 1)
            self._draw_custom_setting()

        def down():
            field = self._custom_setting_fields[self._custom_setting_index]
            if field == "work":
                self.custom.set_work_minutes(self.custom.work_minutes - 1)
            elif field == "break":
                self.custom.set_break_minutes(self.custom.break_minutes - 1)
            elif field == "cycles":
                self.custom.set_total_cycles(self.custom.total_cycles - 1)
            self._draw_custom_setting()

        def next_field():
            self._custom_setting_index += 1
            if self._custom_setting_index >= len(self._custom_setting_fields):
                self._start_custom()
            else:
                self._draw_custom_setting()

        self.buttons.register(UP, up)
        self.buttons.register(DOWN, down)
        self.buttons.register(SELECT, next_field)
        self.buttons.register(BACK, lambda: self.menu.back())

    def _start_custom(self) -> None:
        self.custom.on_phase_change = self._on_custom_phase
        self.custom.on_all_done = self._on_custom_all_done
        self.custom.start()
        # Initial start: set steady color (no flash)
        if self.custom.phase == CustomPhase.WORK:
            self.backlight.set_state("work")
        else:
            self.backlight.set_state("break")
        r, g, b = self.backlight.current_color
        self.blinkstick.set_color(r, g, b)
        self._bind_timer_buttons()
        self.buttons.register(PLUS, self._skip_custom_phase)

    def _skip_custom_phase(self) -> None:
        self.custom.skip()
        # If skip triggered on_all_done, don't rebind timer buttons
        if self.custom.current_cycle >= self.custom.total_cycles and self.custom.phase == CustomPhase.WORK:
            return
        self._update_custom_visuals()
        self._bind_timer_buttons()
        self.buttons.register(PLUS, self._skip_custom_phase)

    def _on_custom_phase(self, phase: CustomPhase, cycle: int, total: int) -> None:
        self._update_custom_visuals()

    def _update_custom_visuals(self) -> None:
        if self.custom.phase == CustomPhase.WORK:
            self.backlight.set_state("work")
        else:
            self.backlight.set_state("break")
        r, g, b = self.backlight.current_color
        self.blinkstick.flash(r, g, b, count=3)

    def _on_custom_all_done(self) -> None:
        self.backlight.set_state("done")
        self.blinkstick.flash(0, 128, 0, count=5)
        self.display.draw_message("All Done!", f"{self.custom.total_cycles} cycles complete")
        self.buttons.clear_handlers()
        for btn in range(6):
            self.buttons.register(btn, self._show_main_menu)

    # ── Common Timer Controls ──

    def _bind_timer_buttons(self) -> None:
        self.buttons.clear_handlers()
        self.buttons.register(SELECT, self._toggle_pause)
        self.buttons.register(BACK, self._stop_and_menu)

    def _toggle_pause(self) -> None:
        if self.timer.state == TimerState.RUNNING:
            self.timer.pause()
            self.backlight.set_state("paused")
            self.blinkstick.set_color(128, 100, 0)
        elif self.timer.state == TimerState.PAUSED:
            self.timer.resume()
            # Restore mode-appropriate color
            if self._active_mode == "pomodoro":
                self._update_pomodoro_visuals()
            elif self._active_mode == "countdown":
                self.backlight.set_state("work")
                r, g, b = self.backlight.current_color
                self.blinkstick.set_color(r, g, b)
            elif self._active_mode == "custom":
                self._update_custom_visuals()

    def _stop_and_menu(self) -> None:
        self.menu.back()

    # ── Timer Events ──

    def _on_timer_done(self) -> None:
        """Central done dispatcher — routes to the active mode's completion handler."""
        mode = self._active_mode
        if mode == "pomodoro":
            self.pomodoro._on_timer_done()
        elif mode == "countdown":
            self._on_countdown_done()
        elif mode == "custom":
            self.custom._on_timer_done()

    def _on_tick(self, remaining: float) -> None:
        duration = self.timer.duration
        if self._active_mode == "pomodoro":
            screens.render_pomodoro(
                self.display, remaining, self.pomodoro.phase, self.pomodoro.completed_cycles, duration
            )
        elif self._active_mode == "countdown":
            screens.render_countdown(self.display, remaining, self.timer.state)
        elif self._active_mode == "custom":
            screens.render_custom(
                self.display, remaining, self.custom.phase,
                self.custom.current_cycle, self.custom.total_cycles, duration
            )

    def _on_timer_state_change(self, state: TimerState) -> None:
        if state == TimerState.PAUSED:
            self.backlight.set_state("paused")


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()

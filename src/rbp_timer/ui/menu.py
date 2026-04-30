"""Main menu and navigation state machine."""

from __future__ import annotations

import enum
from typing import Callable, List, Optional


class MenuState(enum.Enum):
    MAIN = "main"
    TIMER = "timer"
    SETTINGS = "settings"


class Menu:
    """Navigation state machine for the timer UI."""

    MAIN_ITEMS = ["Pomodoro", "Custom Pomodoro", "Countdown Timer", "Status Light"]
    _MODE_KEYS = ["pomodoro", "custom", "countdown", "status_light"]

    def __init__(self):
        self._state = MenuState.MAIN
        self._selected_index = 0

        # Callbacks
        self.on_mode_selected: Optional[Callable[[str], None]] = None
        self.on_back_to_menu: Optional[Callable[[], None]] = None
        self.on_redraw: Optional[Callable[[], None]] = None

    @property
    def state(self) -> MenuState:
        return self._state

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_mode(self) -> str:
        return self._MODE_KEYS[self._selected_index]

    def navigate_up(self) -> None:
        if self._state == MenuState.MAIN:
            self._selected_index = (self._selected_index - 1) % len(self.MAIN_ITEMS)
            if self.on_redraw:
                self.on_redraw()

    def navigate_down(self) -> None:
        if self._state == MenuState.MAIN:
            self._selected_index = (self._selected_index + 1) % len(self.MAIN_ITEMS)
            if self.on_redraw:
                self.on_redraw()

    def select(self) -> None:
        """Select the currently highlighted item."""
        if self._state == MenuState.MAIN:
            self._state = MenuState.TIMER
            if self.on_mode_selected:
                self.on_mode_selected(self.selected_mode)

    def back(self) -> None:
        """Go back to the main menu."""
        if self._state in (MenuState.TIMER, MenuState.SETTINGS):
            self._state = MenuState.MAIN
            if self.on_back_to_menu:
                self.on_back_to_menu()

    def enter_settings(self) -> None:
        self._state = MenuState.SETTINGS

    def exit_settings(self) -> None:
        self._state = MenuState.TIMER

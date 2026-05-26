# Copilot Instructions — rbp-timer

## Build & Test

```bash
# Install (editable, in venv)
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Run all tests
.venv/bin/pytest

# Run a single test file or class
.venv/bin/pytest tests/test_timer.py
.venv/bin/pytest tests/test_modes.py::TestPomodoroMode

# Run a single test
.venv/bin/pytest tests/test_timer.py::TestTimerStates::test_pause_transitions_to_paused
```

No linter is configured.

## Architecture

This is a headless productivity timer for Raspberry Pi with a Pimoroni GFX HAT (128×64 LCD + 6 capacitive buttons) and BlinkStick Square USB LED. It runs as a systemd service and is controlled entirely via hardware buttons.

### Layer separation

```
main.py (App)         — wires everything together, owns the event loop
├── timer.py          — pure countdown engine (no hardware deps), thread-safe
├── modes/            — mode logic (Pomodoro, Custom, Countdown, StatusLight)
│   └── each mode configures the shared Timer and reacts to its callbacks
├── hardware/         — thin wrappers around device APIs (display, backlight, buttons, blinkstick)
└── ui/
    ├── menu.py       — navigation state machine (MenuState enum)
    └── screens.py    — stateless render functions that bridge mode state → display
```

### Key design patterns

- **Shared Timer engine**: All countdown modes share a single `Timer` instance. Modes configure it via `set_duration()` and react via `on_tick`/`on_done` callbacks. The `on_done` callback in `App` dispatches to the active mode's handler.
- **Callback wiring**: `App.__init__` sets `timer.on_done = self._on_timer_done` once. That method dispatches to `pomodoro._on_timer_done()`, `custom._on_timer_done()`, or `self._on_countdown_done()` based on `self._active_mode`. Modes must not set `timer.on_done` themselves.
- **StatusLight is different**: It doesn't use the shared `Timer` — it's a count-up clock with its own `_status_light_tick_loop` thread in `App`.
- **Hardware graceful degradation**: All hardware modules use try/except on import (`gfxhat`, `blinkstick`, `smbus`). When hardware is absent (dev machine), everything runs without errors.
- **Thread safety**: `Timer`, `Display`, `Buttons`, and `StatusLightMode` each use internal locks. Button handlers are dispatched in separate threads to avoid blocking I2C polling.
- **Display rendering**: Uses Pillow `ImageDraw` to compose frames on a 128×64 monochrome image, then blits pixel-by-pixel to `lcd.set_pixel()`. Use `display.begin_frame()` context manager for multi-draw atomic frames.

## Conventions

- **`from __future__ import annotations`** at the top of every module.
- All public state is exposed via `@property`; internal state uses `_` prefix.
- Enums for all state types: `TimerState`, `PomodoroPhase`, `CustomPhase`, `StatusLightState`, `MenuState`.
- Color palettes are separate dicts: `BACKLIGHT_COLORS` (in `backlight.py`) and `BLINKSTICK_COLORS` (in `blinkstick_ctrl.py`).
- Custom Pomodoro settings persist to `~/.config/rbp-timer/custom.json` via atomic write (write to `.tmp`, then `os.replace`).
- Button constants (`UP`, `DOWN`, `BACK`, `MINUS`, `SELECT`, `PLUS`) are module-level in `buttons.py`, imported by name.
- Tests use `FakeClock` (injectable `clock` callable) for deterministic time in `StatusLightMode`; other timer tests use short real durations with `time.sleep`.

## Hardware notes

- **CAP1166 buttons**: The `gfxhat.touch` GPIO interrupt doesn't work on newer Pi kernels. `buttons.py` polls the I2C sensor register (`0x03`) directly at 50ms intervals and clears the INT flag manually.
- **BlinkStick Square**: Must use `set_mode(2)` (WS2812) and address LEDs with `channel=0, index=0..7`. Brightness is capped at 25% via `_BRIGHTNESS` scalar.
- **LCD**: 128×64 monochrome via SPI. No `lcd.contrast()` exists — don't try to call it.

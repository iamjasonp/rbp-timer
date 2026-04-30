# Raspberry Pi Productivity Timer

## Problem
Build a headless productivity timer for a Raspberry Pi 4 equipped with a **Pimoroni GFX HAT** (128×64 LCD, RGB backlight, 6 capacitive touch buttons) and a **BlinkStick** USB LED. The timer runs on boot and is controlled entirely via the GFX HAT buttons.

## Timer Modes
1. **Pomodoro** — 25 min work / 5 min short break / 15 min long break (every 4 cycles)
2. **Countdown** — user-configurable one-shot countdown timer
3. **Custom Intervals** — user-defined work/break durations with configurable cycle count

## Hardware Mapping

### GFX HAT LCD (128×64 monochrome)
- Main menu: mode selection (Pomodoro / Countdown / Custom)
- Timer screen: large countdown digits, mode label, cycle count (Pomodoro)
- Settings screens: adjust durations with up/down buttons

### GFX HAT Backlight (6 RGB zones)
| State       | Color  |
|-------------|--------|
| Work        | Green  |
| Break       | Blue   |
| Paused      | Yellow |
| Timer done  | Red    |
| Menu/idle   | White  |

### GFX HAT Buttons (6 capacitive touch pads)
| Button | Menu Context     | Timer Context     |
|--------|-----------------|-------------------|
| Up     | Navigate up      | —                 |
| Down   | Navigate down    | —                 |
| Left   | Back / cancel    | Back to menu      |
| Right  | Select / enter   | —                 |
| A      | —                | Start / Pause     |
| B      | —                | Stop / Reset      |

### BlinkStick
- Steady color mirrors backlight state during active timer
- Pulse/flash animation on timer completion and break-over alerts
- Off when idle/in menu

## Architecture

```
rbp-timer/
├── pyproject.toml            # Project metadata, dependencies
├── README.md                 # Setup & usage instructions
├── src/
│   └── rbp_timer/
│       ├── __init__.py
│       ├── main.py           # Entry point, app lifecycle
│       ├── timer.py          # Timer engine (countdown logic, states)
│       ├── modes/
│       │   ├── __init__.py
│       │   ├── pomodoro.py   # Pomodoro mode config & state machine
│       │   ├── countdown.py  # Simple countdown mode
│       │   └── custom.py     # Custom intervals mode
│       ├── hardware/
│       │   ├── __init__.py
│       │   ├── display.py    # GFX HAT LCD rendering (text, digits, menus)
│       │   ├── backlight.py  # GFX HAT backlight color management
│       │   ├── buttons.py    # GFX HAT capacitive touch input handling
│       │   └── blinkstick.py # BlinkStick LED control & animations
│       └── ui/
│           ├── __init__.py
│           ├── menu.py       # Main menu & navigation state machine
│           └── screens.py    # Timer display, settings screens
├── systemd/
│   └── rbp-timer.service     # systemd unit for auto-start on boot
└── tests/
    ├── __init__.py
    ├── test_timer.py
    └── test_modes.py
```

## Approach
- **Python 3** with `gfxhat` and `blinkstick` libraries
- Timer engine is pure logic (no hardware deps) → easily testable
- Hardware layer is abstracted behind modules in `hardware/`
- UI state machine handles menu navigation and screen transitions
- Rendering uses the `gfxhat.fonts` or Pillow for drawing text/digits on the 128×64 LCD
- systemd service for headless auto-start on boot
- Graceful shutdown on SIGTERM/SIGINT (clean up hardware state)

## Todos

1. **project-setup** — Initialize Python project structure with pyproject.toml, dependencies (gfxhat, blinkstick, Pillow), and directory layout
2. **timer-engine** — Implement the core timer engine (countdown logic, start/pause/resume/stop/reset, state transitions, callbacks)
3. **pomodoro-mode** — Implement Pomodoro mode (25/5/15 cycle logic, auto-advance between work/break, cycle counting)
4. **countdown-mode** — Implement simple countdown mode (configurable duration, one-shot)
5. **custom-mode** — Implement custom intervals mode (configurable work/break durations and cycle count)
6. **display-driver** — Implement GFX HAT LCD rendering (large digits, menu rendering, status text)
7. **backlight-driver** — Implement GFX HAT backlight color management (state-to-color mapping, transitions)
8. **button-input** — Implement GFX HAT button input handling (event registration, debounce, mapping to actions)
9. **blinkstick-driver** — Implement BlinkStick LED control (steady colors, pulse/flash animations, threaded animation loop)
10. **ui-menus** — Implement UI state machine (main menu, settings screens, timer screen, navigation flow)
11. **main-app** — Wire everything together in main.py (init hardware, event loop, signal handling, graceful shutdown)
12. **systemd-service** — Create systemd unit file and installation instructions for auto-start on boot
13. **tests** — Write unit tests for timer engine and mode logic
14. **readme** — Write README with hardware setup, software installation, and usage instructions

## Notes
- The GFX HAT LCD is 128×64 monochrome — use Pillow `ImageDraw` + `ImageFont` for flexible text rendering, then blit pixel data to `lcd.set_pixel()`
- BlinkStick animations should run in a background thread to avoid blocking the timer loop
- The timer engine should be event-driven (callbacks) so the UI can react to state changes
- Custom intervals settings should persist across reboots (simple JSON config file)

## Hardware Setup Instructions

### Raspberry Pi Configuration
1. **Enable I2C and SPI** — required for GFX HAT communication:
   ```bash
   sudo raspi-config nonint do_i2c 0   # Enable I2C
   sudo raspi-config nonint do_spi 0   # Enable SPI
   sudo reboot
   ```
2. **User permissions** — the service user must be in `gpio`, `i2c`, and `spi` groups:
   ```bash
   sudo usermod -aG gpio,i2c,spi $USER
   ```

### GFX HAT Touch Buttons (CAP1166)
The `gfxhat` library's built-in touch module (`gfxhat.touch`) relies on GPIO interrupts via `RPi.GPIO` to detect capacitive touch events. **This does not work reliably on newer Raspberry Pi OS kernels** (tested on Pi 4 with Python 3.13). The GPIO interrupt never fires even though the CAP1166 chip at I2C address `0x2c` is functioning correctly.

**Fix:** `buttons.py` bypasses `gfxhat.touch` and polls the CAP1166 sensor input status register (`0x03`) directly via `smbus` at 50ms intervals. After reading active touches, the interrupt flag in the main control register (`0x00`) must be cleared by writing `main & ~0x01` so the sensor continues updating.

- I2C address: `0x2c`
- Button bit mapping (left to right on the HAT): bit 0 → bit 5
- The `gfxhat.touch.set_led()` function still works fine for controlling button LEDs
- Extra dependencies not pulled in by `gfxhat`: `smbus`, `spidev`

### GFX HAT LCD (ST7567)
- Uses SPI — requires `spidev` package (not pulled in by `gfxhat`)
- No `lcd.contrast()` method exists in the gfxhat API; the LCD works without it
- Initialize with `lcd.clear()` + `lcd.show()` in the Display constructor

### BlinkStick Square (WS2812 LEDs)
The BlinkStick Square has 8 WS2812 addressable LEDs and reports as **variant 4**. It requires:

1. **WS2812 mode** — set on initialization:
   ```python
   stick.set_mode(2)  # WS2812 mode
   ```
2. **Channel/index addressing** — must specify `channel=0` and `index=0..7` for each LED:
   ```python
   stick.set_color(channel=0, index=i, red=r, green=g, blue=b)
   ```
   Using `stick.set_color(red=r, green=g, blue=b)` (without channel/index) does NOT work.
3. **USB permissions** — requires a udev rule for non-root access:
   ```bash
   echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="20a0", ATTR{idProduct}=="41e5", MODE="0666"' | sudo tee /etc/udev/rules.d/85-blinkstick.rules
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
4. **Extra dependency:** `pyusb` (required by `blinkstick` but not declared as a dependency)

### Deployment
1. Copy project to `/opt/rbp-timer`
2. Create venv and install: `/opt/rbp-timer/.venv/bin/pip install -e .`
3. Copy systemd unit: `sudo cp systemd/rbp-timer.service /etc/systemd/system/`
4. Enable and start: `sudo systemctl enable --now rbp-timer`

### Diagnostic Scripts
- `diag_lcd.py` — Tests LCD by drawing a border rectangle
- `diag_touch.py` — Tests CAP1166 touch via raw I2C register reads
- `diag_blinkstick.py` — Tests BlinkStick Square LED addressing
- `diag_buttons_map.py` — Maps physical button positions to I2C bit indices

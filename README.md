# Jasondoro Timer — Raspberry Pi Productivity Timer

A headless productivity timer for Raspberry Pi 4 with **Pimoroni GFX HAT** and **BlinkStick Square** USB LED.

## Features

- **Pomodoro** — 25 min work / 5 min short break / 15 min long break (every 4 cycles), auto-advancing
- **Custom Pomodoro** — set your own work/break durations and cycle count (persisted across reboots)
- **Countdown Timer** — configurable one-shot countdown (1–180 minutes) with live +/− minute adjustment
- **Progress bar** — 5-pixel bar across bottom of LCD tracks elapsed time in Pomodoro modes
- **Button LEDs** — only active buttons are illuminated; unmapped buttons stay dark

### Hardware Feedback

| State   | GFX HAT Backlight | BlinkStick          |
|---------|--------------------|--------------------|
| Work    | Red (50%)          | Steady red (25%)   |
| Break   | Blue (50%)         | Steady blue (25%)  |
| Paused  | Amber (50%)        | Steady amber (25%) |
| Done    | Green (50%)        | Flash green (25%)  |
| Menu    | Gray (full)        | Off                |

## Hardware Requirements

- Raspberry Pi 4 (or 3B+)
- [Pimoroni GFX HAT](https://shop.pimoroni.com/products/gfx-hat) — 128×64 LCD, RGB backlight, 6 capacitive touch buttons
- [BlinkStick Square](https://www.blinkstick.com/) — USB LED controller (8 WS2812 LEDs, variant 4)

## Software Installation

### 1. Enable I2C and SPI

```bash
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo reboot
```

### 2. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3-pip python3-dev libfreetype6-dev libjpeg-dev fonts-dejavu-core python3-venv
```

### 3. Set up user permissions

```bash
sudo usermod -aG gpio,i2c,spi $USER
```

### 4. Set up BlinkStick USB permissions

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="20a0", ATTR{idProduct}=="41e5", MODE="0666"' | sudo tee /etc/udev/rules.d/85-blinkstick.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 5. Clone and install the timer

```bash
cd /opt
sudo git clone <your-repo-url> rbp-timer
sudo chown -R $USER:$USER rbp-timer
cd rbp-timer
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 6. Install as a systemd service (auto-start on boot)

```bash
sudo cp systemd/rbp-timer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rbp-timer
sudo systemctl start rbp-timer
```

### Managing the service

```bash
sudo systemctl status rbp-timer    # Check status
sudo systemctl stop rbp-timer      # Stop
sudo systemctl restart rbp-timer   # Restart
journalctl -u rbp-timer -f         # View logs
```

## Button Controls

Buttons are labeled left to right on the GFX HAT. LEDs light up only for active buttons.

| Button      | Menu Screen      | Pomodoro Timer   | Countdown Timer  | Settings Screen  |
|-------------|------------------|------------------|------------------|------------------|
| ↑ Up (0)    | Navigate up      | —                | —                | +value           |
| ↓ Down (1)  | Navigate down    | —                | —                | −value           |
| ← Back (2)  | —                | Stop & menu      | Stop & menu      | Cancel           |
| − Minus (3) | —                | —                | −1 minute        | —                |
| ○ Select (4)| Select / enter   | Pause / Resume   | Pause / Resume   | Confirm / Next   |
| + Plus (5)  | —                | Skip phase       | +1 minute        | —                |

## Configuration

Custom Pomodoro settings are saved to `~/.config/rbp-timer/custom.json` and persist across reboots.

## Diagnostics

Hardware diagnostic scripts are in the `diagnostics/` directory:

- `diag_lcd.py` — Tests LCD by drawing a border rectangle
- `diag_touch.py` — Tests CAP1166 touch via raw I2C register reads
- `diag_blinkstick.py` — Tests BlinkStick Square LED addressing
- `diag_buttons_map.py` — Maps physical button positions to I2C bit indices

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest
```

## License

MIT

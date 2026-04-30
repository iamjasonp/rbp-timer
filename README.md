# Jasondoro Timer — Raspberry Pi Productivity Timer

A headless productivity timer for Raspberry Pi 4 with **Pimoroni GFX HAT** and **BlinkStick** USB LED.

## Features

- **Pomodoro Timer** — 25 min work / 5 min short break / 15 min long break (every 4 cycles), auto-advancing
- **Countdown Timer** — configurable one-shot countdown (1–180 minutes)
- **Custom Intervals** — set your own work/break durations and cycle count (persisted across reboots)

### Hardware Feedback

| State   | GFX HAT Backlight | BlinkStick         |
|---------|--------------------|--------------------|
| Work    | Green              | Steady green       |
| Break   | Blue               | Steady blue        |
| Paused  | Yellow             | Steady yellow      |
| Done    | Red                | Flash red          |
| Menu    | Dim white          | Off                |

## Hardware Requirements

- Raspberry Pi 4 (or 3B+)
- [Pimoroni GFX HAT](https://shop.pimoroni.com/products/gfx-hat) — 128×64 LCD, RGB backlight, 6 capacitive touch buttons
- [BlinkStick](https://www.blinkstick.com/) — USB LED controller

## Software Installation

### 1. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3-pip python3-dev libfreetype6-dev libjpeg-dev fonts-dejavu-core
```

### 2. Install GFX HAT library

```bash
curl https://get.pimoroni.com/gfxhat | bash
```

### 3. Clone and install the timer

```bash
cd /opt
sudo git clone <your-repo-url> rbp-timer
cd rbp-timer
pip3 install .
```

### 4. Install as a systemd service (auto-start on boot)

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

| Button | Menu Screen           | Timer Screen    |
|--------|-----------------------|-----------------|
| ▲ Up   | Navigate up / +value  | —               |
| ▼ Down | Navigate down / -value| —               |
| ◀ Left | Back / cancel         | Back to menu    |
| ▶ Right| Select / confirm      | —               |
| A      | Select / confirm      | Start / Pause   |
| B      | —                     | Stop / Reset    |

## Configuration

Custom interval settings are saved to `~/.config/rbp-timer/custom.json` and persist across reboots.

## Development

```bash
pip3 install -e ".[dev]"
pytest
```

## License

MIT

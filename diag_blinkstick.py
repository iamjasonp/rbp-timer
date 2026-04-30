"""Test BlinkStick Square - 8 WS2812 LEDs."""
from blinkstick import blinkstick
import time

sticks = blinkstick.find_all()
print(f"Found {len(sticks)} BlinkStick(s)", flush=True)
for s in sticks:
    print(f"  serial={s.get_serial()}, mode={s.get_mode()}", flush=True)

    # BlinkStick Square needs WS2812 mode (mode 2)
    print("  Setting mode 2 (WS2812)...", flush=True)
    s.set_mode(2)
    time.sleep(0.5)

    # Light all 8 LEDs red
    print("  ALL RED...", flush=True)
    for i in range(8):
        s.set_color(channel=0, index=i, red=255, green=0, blue=0)
    time.sleep(2)

    # All green
    print("  ALL GREEN...", flush=True)
    for i in range(8):
        s.set_color(channel=0, index=i, red=0, green=255, blue=0)
    time.sleep(2)

    # All blue
    print("  ALL BLUE...", flush=True)
    for i in range(8):
        s.set_color(channel=0, index=i, red=0, green=0, blue=255)
    time.sleep(2)

    # Turn off
    for i in range(8):
        s.set_color(channel=0, index=i, red=0, green=0, blue=0)
    print("  Done — did you see red/green/blue?", flush=True)

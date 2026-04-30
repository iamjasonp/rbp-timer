"""Identify which physical button maps to which I2C bit."""
import time
from smbus import SMBus

bus = SMBus(1)
ADDR = 0x2c

bus.write_byte_data(ADDR, 0x21, 0b00111111)
bus.write_byte_data(ADDR, 0x26, 0b00111111)
bus.write_byte_data(ADDR, 0x1F, 0b01000000)

NAMES = {0: "bit0", 1: "bit1", 2: "bit2", 3: "bit3", 4: "bit4", 5: "bit5"}
print("Press each button ONE AT A TIME. 30 seconds to map all 6.", flush=True)
print("Buttons from left to right on the GFX HAT:", flush=True)

prev = 0
for i in range(300):
    status = bus.read_byte_data(ADDR, 0x03)
    new = status & ~prev
    if new:
        bits = [b for b in range(6) if new & (1 << b)]
        print(f"  PRESSED: bits {bits}  (raw=0b{status:06b})", flush=True)
        main = bus.read_byte_data(ADDR, 0x00)
        bus.write_byte_data(ADDR, 0x00, main & ~0x01)
    prev = status
    time.sleep(0.1)

print("Done.", flush=True)

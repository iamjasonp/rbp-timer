"""Direct I2C touch register read — bypasses GPIO interrupts entirely."""
import time
from smbus import SMBus

bus = SMBus(1)
ADDR = 0x2c

# Read product ID to confirm it's a CAP1166
prod_id = bus.read_byte_data(ADDR, 0xFD)
mfg_id = bus.read_byte_data(ADDR, 0xFE)
print(f"Product ID: 0x{prod_id:02x}, Manufacturer ID: 0x{mfg_id:02x}", flush=True)
print(f"Expected CAP1166: Product=0x55, Manufacturer=0x5D", flush=True)

# Enable all 6 inputs
bus.write_byte_data(ADDR, 0x21, 0b00111111)

# Force recalibration
bus.write_byte_data(ADDR, 0x26, 0b00111111)
bus.write_byte_data(ADDR, 0x1F, 0b01000000)

print("Touch any button now (10s) — reading raw touch registers...", flush=True)
for i in range(40):
    # Read sensor input status register (0x03)
    status = bus.read_byte_data(ADDR, 0x03)
    main = bus.read_byte_data(ADDR, 0x00)
    if status:
        print(f"  t={i*0.25:.1f}s  input_status=0b{status:08b}  main=0x{main:02x}", flush=True)
        # Clear interrupt
        bus.write_byte_data(ADDR, 0x00, main & ~0x01)
    time.sleep(0.25)

print("Done.", flush=True)
for i in range(30):
    time.sleep(0.5)
    # Manually check
    s = cap._interrupt_status()
    if s:
        print(f"  interrupt detected at t={i*0.5}s!", flush=True)

print("Step 7: done", flush=True)

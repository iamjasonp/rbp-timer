"""Quick LCD diagnostic — tests pixel rendering."""
from gfxhat import lcd, backlight

lcd.clear()

# Draw a border
for x in range(128):
    lcd.set_pixel(x, 0, 1)
    lcd.set_pixel(x, 63, 1)
for y in range(64):
    lcd.set_pixel(0, y, 1)
    lcd.set_pixel(127, y, 1)

# Center dot
lcd.set_pixel(64, 32, 1)
lcd.show()
print("LCD test done - you should see a border rectangle")

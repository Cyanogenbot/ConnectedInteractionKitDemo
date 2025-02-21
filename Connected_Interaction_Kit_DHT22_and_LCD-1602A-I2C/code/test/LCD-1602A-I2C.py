# Reference: 
# 	Code: https://stackoverflow.com/questions/75839332/lcd-in-circuitpython-flashing-on-then-off
#	Library: https://github.com/dhalbert/CircuitPython_LCD

import board
import busio

from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode

# i2c protocal setup
print("initialising i2c and looking for address")
i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
i2c.try_lock()
address = i2c.scan()[0]
print(f"found address of i2c '{address}'")

# LCD initialize
i2c.unlock()
lcd = LCD(I2CPCF8574Interface(i2c, address), num_rows=2, num_cols=16)
print("debug: lcd initialised")

# LCD reset
lcd.clear()
print("debug: clearing screen")

# LCD print
message = "\nhalf size??"
lcd.print(message)
print(f"debug: lcd printed '{message}'")
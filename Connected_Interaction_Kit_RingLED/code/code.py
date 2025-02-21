'''
OOCSI Asynchonous communication example
This example on works on devices with an external esp32 module which works with esp32spi

Example boards: Arduino Nano RP2040 Connect
Official page: https://docs.arduino.cc/hardware/nano-rp2040-connect/

Library example esp32spi_simpletest.py:
    https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/
        blob/master/examples/esp32spi_simpletest.py 
        
-------------------
Requirements:
    - Arduino Nano RP2040 Connect with CircuitPython 9.2.4:
          https://circuitpython.org/board/arduino_nano_rp2040_connect/
    - Ring LED:
           https://www.adafruit.com/product/1643

-------------------
Setup:
    - How to set Arduino Nano RP2040 Connect into programming mode?
        1. Hold the onboard button and plug-in cable to connect to computer
        2. A window for the storage of the board should pop up
    - How to upload CircuitPython firmware into the board?
        1. Download the firmware file (.UF2) from [official product page](https://circuitpython.org/board/arduino_nano_rp2040_connect/)
        2. Drag the file into the folder of the board
        3. Wait, and as it's done, a folder named "CIRCUITPY" will pop up
        4. Start coding in code.py

'''

# Import basics
import board
import digitalio
import asyncio

# Get WiFi credentials from secrets.py
from secrets import secrets

# Import ESP32 dependencies (for wifi)
import busio
from adafruit_esp32spi import adafruit_esp32spi

# Import oocsi
from oocsi_esp32spi import OOCSI

# Define led pins
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Define & initialize ESP32 connection pins
esp32_cs = digitalio.DigitalInOut(board.CS1)
esp32_ready = digitalio.DigitalInOut(board.ESP_BUSY)
esp32_reset = digitalio.DigitalInOut(board.ESP_RESET)

# Define ESP32 connection
# Secondary (SCK1) SPI used to connect to WiFi board on Arduino Nano Connect RP2040
spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
print("MAC address: ", esp.mac_address)

# import neopixel
import neopixel

# Define the number of pixels and the pin connected to the LED strip
num_pixels = 12  # Adjust this to the number of LEDs in your strip
pixel_pin = board.D2  # Change this to the pin you are using

# Create a NeoPixel object
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1)

# Function to light up the strip with a color
def light_up_strip(color):
    pixels.fill(color)  # Fill the strip with the specified color
    pixels.show()  # Update the strip

# Function to run when an OOCSI message is received
def receiveEvent(sender, recipient, event):
    height = event['height']
    print('height: ', event['height'])
#     print('from ', sender, ' -> ', event)
    if height < 10:
        light_up_strip((0, 0, 255))  # Blue
    elif height > 30:
        light_up_strip((255, 0, 0))  # Red
    else:
        light_up_strip((0, 255, 0))  # Green


# Check if there is an esp32 module attached and what its firmware version is
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("\nESP32 WiFi Module found.")
    print("Firmware version:", str(esp.firmware_version, "utf-8"))
    print("*" * 40)

# Try to connect to the right network
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except (RuntimeError, ConnectionError, OSError) as e:
        print("\nUnable to establish connection. Are you using a valid password?")
        print("Error message:", e, "\nRetrying...")
        continue

# When a network is found, the esp will reply with its ip address
print("Connected! IP address:", esp.pretty_ip(esp.ip_address))

# Initiate OOCSI connection
# use '/' in the channel or client name will create tree structure of the client node
oocsi = OOCSI("OOCSI/CLIENT/NAME-subtitle", "HOST-NAME-OR-IP-OF-OOCSI-SERVER", esp)

# oocsi.subscribe("testchannel", receiveEvent)
oocsi.subscribe("circuitpython/plane/controller", receiveEvent)

# Define an asynchronous blink function
async def blink():
    while True:
        led.value = True
        await asyncio.sleep(1)
        led.value = False
        await asyncio.sleep(1)

# Define loop
async def loop():
    asyncio.create_task(blink())
    await oocsi.keepAlive()

# Start loop
asyncio.core.run(loop())



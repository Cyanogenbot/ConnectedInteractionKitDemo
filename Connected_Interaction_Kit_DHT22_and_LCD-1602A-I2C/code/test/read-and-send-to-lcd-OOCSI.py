# OOCSI Asynchonous communication example
# This example on works on devices with an external esp32 module which works with esp32spi
# Example boards: RP2040 Nano Connect
# unchecked: Connected Interaction Kit, Lolin S3

# Import basics
import time
import board
import digitalio
import asyncio
import wifi
import json


# Get WiFi credentials from secrets.py
from secrets import secrets

# Import ESP32 dependencies (for wifi)
import busio
# from adafruit_esp32spi import adafruit_esp32spi

# Import oocsi
from oocsi import OOCSI
# from oocsi_esp32spi import OOCSI

# Import DHT
import adafruit_dht

# Define DHT sensor
dht = adafruit_dht.DHT22(board.D2)

# import PCF8574 LCD driver
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode

# i2c protocal setup for LCD
print("initialising i2c and looking for address")
i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
i2c.try_lock()
address = i2c.scan()[0]
print(f"found address of i2c '{address}'")

# LCD initialize
i2c.unlock()
lcd = LCD(I2CPCF8574Interface(i2c, address), num_rows=2, num_cols=16)
print("debug: lcd initialised")


# Function to run when an OOCSI message is received
def receiveEvent(sender, recipient, event):
    print('from ', sender, ' -> ', event)

def scan_network():
#     print(f"\nConnecting to {ssid}...")
#     print(f"Signal Strength: {rssi}")
    for network in wifi.radio.start_scanning_networks():
        if str(network.ssid, "utf-8") == "Router-ID-1.id":
            print("Target network:  %s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
                                             network.rssi, network.channel))
    wifi.radio.stop_scanning_networks()

# network initialization
network = wifi.radio
def connectWifi():
    try:
        scan_network()
        # Connect to the Wi-Fi network
        if network.connected == False:
            print('connecting to network...')
            # replace these by your WIFI name and password
            network.connect(secrets["ssid"], secrets["password"])
            while network.connected == False:
                pass
        # When a network is found, the esp will reply with its ip address
        print("Connected! IP address:", network.ipv4_address)
    except OSError as e:
        print(f"❌ OSError: {e}")
    print("✅ Wifi!")


# Create a task to check for incoming messages from the OOCSI server
async def checkMessages():
    while True:
        try:
            await oocsi.asyncCheck()
        except Exception as e:
            print(f"Error in checkMessages: {str(e)}")
        await asyncio.sleep(0.5)


def read_DHT_to_LCD():
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        msg_json = {'Temp': temperature , 'Humidity': humidity}
        oocsi.send('eden-circuitpython-test', msg_json)
        msg = json.dumps(msg_json, separators = (',', ':'))
        print(msg)
        
        # LCD reset - every time before print
        lcd.clear()
        print("debug: clearing screen")
        
        # LCD print
        lcd.print("Temp: {:.1f} *C \t Humidity: {}%".format(temperature, humidity))
#         print(f"debug: lcd printed '{message}'")
    except RuntimeError as e:
        # Reading doesn't always work! Just print error and we'll try again
        print("Reading from DHT failure: ", e.args)

# sending message asynchronously
async def sendMessages():
    while True:
        read_DHT_to_LCD()
        await asyncio.sleep(1)


#---------------------------------------------------------------------------
# create Wifi connection
connectWifi()

# Initiate OOCSI connection
oocsi = OOCSI("eden-circuitpython-test-####", "hello.oocsi.net")
oocsi.subscribe("testchannel", receiveEvent)


# Define loop
async def loop():
    # Create tasks to check for incoming messages and send messages
    messages = asyncio.create_task(checkMessages())
    send_message = asyncio.create_task(sendMessages())

    # Run both tasks at the same time independently from eachother
    await asyncio.gather(messages, send_message)

# Start loop
asyncio.core.run(loop())

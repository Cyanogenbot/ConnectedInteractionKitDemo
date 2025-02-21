'''
OOCSI Asynchonous communication example

This example works on devices with wifi module prebuilt in CircuitPython firmware

Example boards: Arduino Nano ESP32
Official page: https://docs.arduino.cc/hardware/nano-esp32
Possible applied boards: Pyboards with wifi library prebuilt in the CircuitPython firmware

Reference:
    https://github.com/iddi/oocsi-circuitpython/blob/main/Examples/async_oocsi_example.py

Author: edenchiang

-------------------
Requirements:
    - Arduino Nano ESP32 with CircuitPython 9.2.4:
          https://circuitpython.org/board/arduino_nano_esp32s3/
    - HT22 module:
           https://github.com/adafruit/Adafruit_CircuitPython_DHT
    - 1602A LCD display (I2C version):
           https://github.com/dhalbert/CircuitPython_LCD

-------------------
Setup:
    - How to set Arduino Nano ESP32 into programming mode?
        1. Connect the board to the computer
        2. Shortage GND pin and B1 pin with jumper wire, then the onboard LED will turn into GREEN
        3. Press the onboard RST button, the onboard LED stays GREEN
        4. Remove the shortage of GND pin and B1 pin, the onboard LED will turn into dark purple
        5. Done! It's in programming mode now
    - How to upload CircuitPython firmware into the board?
        1. Set the board into programming mode (follow the instructions above)
        2. Open https://circuitpython.org/board/arduino_nano_esp32s3/
        3. Click the "OPEN INSTALLER" button below the "DOWNLOAD" buttons
            a. Choose "Install CircuitPython 9.2.4 Bin Only" 
            b. Click "Next"
            c. Click "Connect", if the board has been put into programming mode successfully,
               the window for next step will popup, otherwise, re-do the procedure abocve for 
               putting the board into programming mode
            d. Choose the correct COM port connecting to the board
            e. "Continue" to overwrite
            f. Done, the CIRCUITPY folder of the board will pop up
            g. Start coding or uploading programs

'''

# Import basics
import time
import board
import digitalio
import asyncio
import wifi
import json
import busio

# Get WiFi credentials from secrets.py
from secrets import secrets

# Import oocsi
from oocsi import OOCSI

# setup DHT sensor
import adafruit_dht
dht = adafruit_dht.DHT22(board.D2)

# i2c protocal setup for PCF8574 LCD
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode
print("initialising i2c and looking for address")
# SDA - A4, SCL - A5
i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
i2c.try_lock()
address = i2c.scan()[0]
print(f"found address of i2c '{address}'")
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
        if str(network.ssid, "utf-8") == secrets["ssid"]:
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
            print('connecting to network: ', secrets["ssid"])
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
        # use '/' in the channel will create tree structure of the channel
        oocsi.send('circuitpython/plane/controller', msg_json)
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
# use '/' in the channel will create tree structure of the client node
oocsi = OOCSI("OOCSI/CLIENT/NAME-subtitle", "HOST-NAME-OR-IP-OF-OOCSI-SERVER")



# Define loop
async def loop():
    # Create tasks to check for incoming messages and send messages
    send_message = asyncio.create_task(sendMessages())

    # Run both tasks at the same time independently from eachother
    await asyncio.gather(send_message)

# Start loop
asyncio.core.run(loop())


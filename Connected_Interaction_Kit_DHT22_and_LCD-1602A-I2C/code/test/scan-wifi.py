'''
Sample code for Wi-Fi scan with wifi module integrated CircuitPython boards
'''

import wifi
from secrets import secrets

# Search for available networks
print("Available WiFi networks:")

for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
                                             network.rssi, network.channel))

wifi.radio.stop_scanning_networks()

# Connect to the desired WiFi networks
#wifi.radio.connect(secrets["ssid"]), secrets["password"]))
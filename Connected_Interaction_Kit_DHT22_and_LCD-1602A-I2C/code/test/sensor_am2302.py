# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT
#
# reference: https://learn.adafruit.com/dht/dht-circuitpython-code

import time

import board
import adafruit_dht

# data pin setting for DHT sensor
dht = adafruit_dht.DHT22(board.D2)

# main loop
while True:
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        # Print what we got to the REPL
        print("Temp: {:.1f} *C \t Humidity: {}%".format(temperature, humidity))
    except RuntimeError as e:
        # Reading doesn't always work! Just print error and we'll try again
        print("Reading from DHT failure: ", e.args)

    time.sleep(1)
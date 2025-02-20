# Import basics
import board
import digitalio
import time
import asyncio

# Get WiFi credentials from secrets.py
from secrets import secrets

# Import ESP32 dependencies (for wifi)
import busio
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_socketpool

# Import Sensor
import busio
import adafruit_vl53l0x
import bmi160 as BMI160
import math

# Initiate Distance Sensor and Gyro
i2c_port = busio.I2C(board.SCL, board.SDA)
i2c = i2c_port  # uses board.SCL and board.SDA

bmi = BMI160.BMI160(i2c)
dist_sensor = adafruit_vl53l0x.VL53L0X(i2c_port)

# Define & initialize ESP32 connection pins
esp32_cs = digitalio.DigitalInOut(board.D9)
esp32_ready = digitalio.DigitalInOut(board.D11)
esp32_reset = digitalio.DigitalInOut(board.D12)

# Define ESP32 connection
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)


# Check if there is an esp32 module attached and what its firmware version is
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("\nESP32 WiFi Module found.")
    print("Firmware version:", str(esp.firmware_version, "utf-8"))
    print("*" * 40)

# Check if the right network available, and if not, shut down.
print("\nScanning for available networks...\n")


network_list = []
for ap in esp.scan_networks():
    network_list.append(str(ap.ssid, "utf-8"))
print(network_list)

if secrets["ssid"] not in network_list:
    print(secrets["ssid"], "not found. \nAvailable networks:", network_list)
    raise SystemExit(0)

# Try to connect to the right network
print(secrets["ssid"], "found. Connecting...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except (RuntimeError, ConnectionError, OSError) as e:
        print("\nUnable to establish connection. Are you using a valid password?")
        print("Error message:", e, "\nRetrying...")
        continue

# When a network is found, the esp will reply with its ip address
print("Connected! IP address:", esp.pretty_ip(esp.ip_address))

def receiveEvent(sender, recipient, event):
    print('from ', sender, ' -> ', event)

# Import oocsi
from oocsi_esp32spi import OOCSI

oocsi = OOCSI("test/diede/Connected_Interaction_Kit_##", "gimme.oocsi.net", esp)
oocsi.subscribe("testchannel", receiveEvent)
# after connecting to the wifi the main loop starts which checks its connection to DataFoundry

# Constants for complementary filter
dt = 0.01  # 10ms sample rate
alpha = 0.96  # filter coefficient

# Initialize angles
roll = 0.0
pitch = 0.0
yaw = 0.0



# Initialize variables
dt = 0.01  # 10ms sample rate
yaw = 0.0  # Simple integration for yaw
last_time = time.monotonic()

class KalmanFilter:
    def __init__(self):
        # State vector [angle, bias]
        self.angle = 0.0
        self.bias = 0.0

        # Error covariance matrix
        self.P = [[0.0, 0.0], [0.0, 0.0]]

        # Process noise
        self.Q_angle = 0.001
        self.Q_bias = 0.003

        # Measurement noise
        self.R_measure = 0.03

    def update(self, measurement, rate, dt):
        # Predict
        self.angle += dt * (rate - self.bias)

        # Update error covariance matrix
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.Q_angle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.Q_bias * dt

        # Calculate Kalman gain
        S = self.P[0][0] + self.R_measure
        K = [self.P[0][0] / S, self.P[1][0] / S]

        # Update state
        angle_error = measurement - self.angle
        self.angle += K[0] * angle_error
        self.bias += K[1] * angle_error

        # Update error covariance matrix
        P00_temp = self.P[0][0]
        P01_temp = self.P[0][1]

        self.P[0][0] -= K[0] * P00_temp
        self.P[0][1] -= K[0] * P01_temp
        self.P[1][0] -= K[1] * P00_temp
        self.P[1][1] -= K[1] * P01_temp

        return self.angle

kalman_roll = KalmanFilter()
kalman_pitch = KalmanFilter()

def calculate_angles():
    global yaw, last_time

    current_time = time.monotonic()
    dt = current_time - last_time
    last_time = current_time

    # Read sensor data
    gyro = bmi.gyro     # Already in degrees/second
    accel = bmi.acceleration  # in m/s^2

    # Extract components
    gyro_x, gyro_y, gyro_z = gyro  # Already in degrees/second
    accel_x, accel_y, accel_z = accel

    # Calculate angles from accelerometer (result in degrees)
    accel_roll = math.atan2(accel_y, math.sqrt(accel_x * accel_x + accel_z * accel_z)) * 180.0 / math.pi
    accel_pitch = math.atan2(-accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * 180.0 / math.pi

    # Update Kalman filters (all values in degrees)
    roll = kalman_roll.update(accel_roll, gyro_x, dt)    # Returns degrees
    pitch = kalman_pitch.update(accel_pitch, gyro_y, dt) # Returns degrees

    # Update yaw by integrating gyro_z (already in degrees/second)
    yaw += gyro_z * dt  # Result in degrees

    # Normalize yaw to -180 to +180 degrees
    yaw = ((yaw + 180) % 360) - 180

    return roll, pitch, yaw

while True:
    ## oocsi.check()
    angles = calculate_angles()
    message = {}
    message["roll"] = angles[1]
    message["pitch"] = angles[0]
    message["yaw"] = angles[2]
    message["height"] = dist_sensor.range / 120 * 10
    oocsi.send("circuitpython/plane/controller", message)
    time.sleep(0.1)


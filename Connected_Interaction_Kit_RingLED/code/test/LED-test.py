import board
import neopixel
import time

# Define the number of pixels and the pin connected to the LED strip
num_pixels = 12  # Adjust this to the number of LEDs in your strip
pixel_pin = board.D2  # Change this to the pin you are using

# Create a NeoPixel object
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1)

# Function to light up the strip with a color
def light_up_strip(color):
    pixels.fill(color)  # Fill the strip with the specified color
    pixels.show()  # Update the strip

# Example usage
while True:
    light_up_strip((255, 0, 0))  # Red
    time.sleep(1)
    light_up_strip((0, 255, 0))  # Green
    time.sleep(1)
    light_up_strip((0, 0, 255))  # Blue
    time.sleep(1)
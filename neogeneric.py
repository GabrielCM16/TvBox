import os
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import neopixel

os.environ["BLINKA_FORCEBOARD"] = "GENERIC_LINUX"

PIXEL_PIN = Pin((1, 10))
strip = neopixel.NeoPixel(PIXEL_PIN, 8, brightness=0.2, auto_write=True)

strip[0] = (255, 0, 0)  # Acende vermelho no primeiro pixel

# rodando com sudo ./.env/bin/python3 ./blink.py

import os

os.environ["BLINKA_FORCEBOARD"]="ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"]="RK3328"

from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import board
import digitalio
import time

pin = Pin((1,10))  # (x,y) = 32*x + 10*y  -> 1*32 + 10 = 42 (GPIO 42)

print("hello blinky!")

led = digitalio.DigitalInOut(pin)
led.direction = digitalio.Direction.OUTPUT

while True:
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)
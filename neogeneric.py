import os
import time
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import neopixel


os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

# Configura o pino GPIO
PIXEL_PIN = Pin((1, 10))   # GPIO 42
PIXEL_COUNT = 8            # Número de LEDs NeoPixel (ajuste para o seu caso)
BRILHO = 0.2               # Brilho

# Inicializa o NeoPixel
pixels = neopixel.NeoPixel(
    PIXEL_PIN, PIXEL_COUNT,
    brightness=BRILHO,
    auto_write=False,
    pixel_order=neopixel.GRB
)

print("Hello NeoPixel!")

# Loop simples piscando cores
while True:
    # Todos em vermelho
    pixels.fill((255, 0, 0))
    pixels.show()
    time.sleep(0.5)

    # Todos em verde
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(0.5)

    # Todos em azul
    pixels.fill((0, 0, 255))
    pixels.show()
    time.sleep(0.5)

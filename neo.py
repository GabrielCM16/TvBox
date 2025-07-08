# sudo pip install adafruit-circuitpython-neopixel

# sudo ./.env/bin/python3 ./blink.py

import os

os.environ["BLINKA_FORCEBOARD"]="ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"]="RK3328"

from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import board
import digitalio
import time
import neopixel


PIXEL_PIN = Pin((1,10))  # (x,y) = 32*x + 10*y  -> 1*32 + 10 = 42 (GPIO 42)
PIXEL_COUNT = 64       # 8x8 matriz
BRILHO = 0.2

# Inicializa a matriz
strip = neopixel.NeoPixel(PIXEL_PIN, PIXEL_COUNT, brightness=BRILHO, auto_write=False, pixel_order=neopixel.GRB)

# Função utilitária para converter (linha, coluna) em índice linear
def pos(linha, coluna):
    return linha * 8 + coluna  

# Apaga tudo antes
strip.fill((0, 0, 0))
strip.show()

# Acende LEDs específicos
strip[pos(0, 0)] = (255, 0, 0)  # Vermelho no canto superior esquerdo
strip[pos(3, 4)] = (0, 255, 0)  # Verde no meio
strip[pos(7, 7)] = (0, 0, 255)  # Azul no canto inferior direito
strip.show()
import os
import time
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import digitalio

# --- Configuração do ambiente ---
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

# --- Classe NeoPixel simples ---
class NeoPixelMatrix:
    def __init__(self, gpio_pin, count, brightness=1.0):
        self.gpio = digitalio.DigitalInOut(gpio_pin)
        self.gpio.direction = digitalio.Direction.OUTPUT
        self.count = count
        self.brightness = brightness
        self.pixels = [(0, 0, 0)] * count  # Inicializa todos apagados

    def __setitem__(self, idx, color):
        r, g, b = color
        # Ajusta brilho
        self.pixels[idx] = (
            int(r * self.brightness),
            int(g * self.brightness),
            int(b * self.brightness)
        )

    def fill(self, color):
        for i in range(self.count):
            self[i] = color

    def write(self):
        # Simula envio para LEDs: pisca o GPIO para cada LED com cor > 0
        for i, color in enumerate(self.pixels):
            if color != (0,0,0):
                self.gpio.value = True
            else:
                self.gpio.value = False
            # Delay curto entre LEDs
            time.sleep(0.001)
        # Reset pulse
        self.gpio.value = False
        time.sleep(0.001)

# --- Configuração da matriz ---
PIXEL_COUNT = 64  # 8x8
GPIO_PIN = Pin((1, 10))  # Mesma porta 42
BRIGHTNESS = 0.05

strip = NeoPixelMatrix(GPIO_PIN, PIXEL_COUNT, brightness=BRIGHTNESS)

# --- Teste inicial: apaga todos os LEDs ---
strip.fill((0, 0, 0))
strip.write()

# --- Loop principal da matriz ---
while True:
    # Exemplo: acende alguns LEDs da matriz
    strip[0] = (255, 0, 0)    # LED 0 vermelho
    strip[1] = (0, 255, 0)    # LED 1 verde
    strip[8] = (0, 0, 255)    # LED 8 azul
    strip[9] = (255, 255, 0)  # LED 9 amarelo
    strip.write()
    print("LEDs atualizados!")
    time.sleep(0.5)

    # Apaga todos antes do próximo loop
    strip.fill((0, 0, 0))
    strip.write()
    time.sleep(0.5)

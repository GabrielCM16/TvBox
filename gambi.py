import time
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import digitalio

# --- Classe NeoPixel Custom ---
class NeoPixelMatrix:
    def __init__(self, pin, count, brightness=1.0):
        self.gpio = digitalio.DigitalInOut(pin)
        self.gpio.direction = digitalio.Direction.OUTPUT
        self.count = count
        self.brightness = brightness
        self.pixels = [(0, 0, 0)] * count

    def __setitem__(self, idx, color):
        r, g, b = color
        self.pixels[idx] = (
            int(r * self.brightness),
            int(g * self.brightness),
            int(b * self.brightness)
        )

    def fill(self, color):
        for i in range(self.count):
            self[i] = color

    def write(self):
        # Envia cada LED na ordem GRB
        for color in self.pixels:
            self._send_byte(color[1])  # G
            self._send_byte(color[0])  # R
            self._send_byte(color[2])  # B
        # Reset pulse > 50 µs
        time.sleep(0.001)

    def _send_byte(self, byte):
        for i in range(8):
            if byte & (1 << (7-i)):
                self._send_one()
            else:
                self._send_zero()

    def _send_one(self):
        # Aproxima o tempo para '1' (não exato, apenas teste)
        self.gpio.value = True
        time.sleep(0.0000008)
        self.gpio.value = False
        time.sleep(0.00000045)

    def _send_zero(self):
        # Aproxima o tempo para '0' (não exato, apenas teste)
        self.gpio.value = True
        time.sleep(0.0000004)
        self.gpio.value = False
        time.sleep(0.00000085)

# --- Configuração da Matriz ---
PIXEL_PIN = Pin((1, 16))  # Mapeamento para GPIO48 (confirme)
PIXEL_COUNT = 64           # 8x8
BRIGHTNESS = 0.05

strip = NeoPixelMatrix(PIXEL_PIN, PIXEL_COUNT, brightness=BRIGHTNESS)

# --- Teste inicial ---
strip.fill((0, 0, 0))
strip.write()
time.sleep(0.5)

# --- Loop de LEDs ---
while True:
    strip[0] = (255, 0, 0)    # Vermelho
    time.sleep(0.1)
    strip[1] = (0, 255, 0)    # Verde
    time.sleep(0.1)
    strip[8] = (0, 0, 255)    # Azul
    time.sleep(0.1)
    strip[9] = (255, 255, 0)  # Amarelo
    strip.write()
    print("LEDs atualizados!")
    time.sleep(0.5)

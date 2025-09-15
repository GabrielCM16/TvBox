import os
import time
import neopixel
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin

# Força Blinka a usar a placa correta
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

# GPIO42 = Pin((1,10))
PIXEL_PIN = Pin((1,10))  
PIXEL_COUNT = 64      # 8x8
BRIGHTNESS = 0.1      # menor brilho para reduzir sobrecarga do GPIO

# Inicializa NeoPixel
pixels = neopixel.NeoPixel(PIXEL_PIN, PIXEL_COUNT, brightness=BRIGHTNESS, auto_write=True, pixel_order=neopixel.GRB)

# Função utilitária para converter (linha, coluna) em índice linear
def pos(linha, coluna):
    return linha * 8 + coluna  

# Função para acender a matriz lentamente
def test_matrix():
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
    for linha in range(8):
        for coluna in range(8):
            pixels[pos(linha, coluna)] = colors[(linha + coluna) % len(colors)]
            pixels.show()
            time.sleep(0.05)  # pequeno delay entre LEDs para minimizar erros de timing
    time.sleep(1)
    pixels.fill((0,0,0))
    pixels.show()
    time.sleep(1)

# Loop principal
try:
    while True:
        test_matrix()
except KeyboardInterrupt:
    pixels.fill((0,0,0))
    pixels.show()

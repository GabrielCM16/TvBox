import os
import time
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import neopixel

# Força o Blinka para sua placa
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

PIXEL_PIN = Pin((1,10))  # Seu pino GPIO 42
PIXEL_COUNT = 64         # Matriz 8x8
BRILHO = 0.2             # Ajuste de brilho (0 a 1)

strip = neopixel.NeoPixel(
    PIXEL_PIN,
    PIXEL_COUNT,
    brightness=BRILHO,
    auto_write=False,
    pixel_order=neopixel.GRB
)

# Função para converter coordenadas (linha, coluna) para índice linear
def pos(linha, coluna):
    return linha * 8 + coluna

# Apaga todos os LEDs
strip.fill((0, 0, 0))
strip.show()

# Exemplo: acende 3 LEDs em posições diferentes da matriz
strip[pos(0, 0)] = (255, 0, 0)  # Vermelho canto superior esquerdo
strip[pos(3, 4)] = (0, 255, 0)  # Verde no meio da matriz
strip[pos(7, 7)] = (0, 0, 255)  # Azul canto inferior direito
strip.show()

# Exemplo simples de animação: percorre a matriz acendendo LEDs
while True:
    for i in range(PIXEL_COUNT):
        strip.fill((0, 0, 0))
        strip[i] = (255, 255, 0)  # Amarelo
        strip.show()
        time.sleep(0.1)

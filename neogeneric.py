import os
import time
import neopixel
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin

# Força modo genérico do Blinka
os.environ["BLINKA_FORCEBOARD"] = "GENERIC_LINUX"

# Configuração do NeoPixel
PIXEL_PIN = Pin((1, 10))   # (x, y) = 32*x + 10*y  -> 1*32 + 10 = 42 (GPIO 42)
PIXEL_COUNT = 64           # Exemplo: matriz 8x8
BRILHO = 0.2               # Brilho dos LEDs

# Inicializa a matriz
strip = neopixel.NeoPixel(
    PIXEL_PIN,
    PIXEL_COUNT,
    brightness=BRILHO,
    auto_write=False,
    pixel_order=neopixel.GRB
)

# Função utilitária para converter (linha, coluna) em índice linear
def pos(linha, coluna):
    return linha * 8 + coluna

# Apaga todos os LEDs antes de iniciar
strip.fill((0, 0, 0))
strip.show()

# Acende LEDs específicos
strip[pos(0, 0)] = (255, 0, 0)   # Vermelho no canto superior esquerdo
strip[pos(3, 4)] = (0, 255, 0)   # Verde no meio
strip[pos(7, 7)] = (0, 0, 255)   # Azul no canto inferior direito
strip.show()

# Animação simples (opcional)
for i in range(PIXEL_COUNT):
    strip.fill((0, 0, 0))
    strip[i] = (255, 255, 0)
    strip.show()
    time.sleep(0.05)

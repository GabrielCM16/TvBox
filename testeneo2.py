import os
import neopixel
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin

# Força Blinka a usar a placa correta
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

# Pino de teste: GPIO42
PIXEL_PIN = Pin((1,10))  # GPIO42 = (1,10)
PIXEL_COUNT = 8           # Teste com 8 LEDs
BRIGHTNESS = 0.05         # Brilho baixo para reduzir erro de timing

# Inicializa NeoPixel
strip = neopixel.NeoPixel(
    PIXEL_PIN,
    PIXEL_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,      # vamos usar write() manual
    pixel_order=neopixel.GRB
)

# Apaga todos os LEDs
strip.fill((0,0,0))
strip.write()

# Acende alguns LEDs fixos
strip[0] = (255,0,0)  # vermelho
strip[1] = (0,255,0)  # verde
strip[2] = (0,0,255)  # azul
strip.write()          # envia sinal para os LEDs

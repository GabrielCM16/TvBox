import os
import time

# Define a placa antes de importar NeoPixel
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

print("Ambiente Blinka configurado para ROC-RK3328-CC / RK3328")

import neopixel
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin

# Configurações básicas
PIXEL_PIN = Pin((1, 10))  # GPIO42
PIXEL_COUNT = 64           # 8x8
BRIGHTNESS = 0.05

print(f"Inicializando NeoPixel com {PIXEL_COUNT} LEDs...")
strip = neopixel.NeoPixel(
    PIXEL_PIN,
    PIXEL_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=neopixel.GRB
)
print("NeoPixel inicializado com sucesso")

# Apaga todos os LEDs
print("Apagando todos os LEDs...")
strip.fill((0, 0, 0))
strip.write()
print("Todos os LEDs apagados")

# Acende alguns LEDs fixos
while True:
    print("Acendendo LEDs: 0-vermelho, 1-verde, 8-azul, 9-amarelo")
    strip[0] = (255, 0, 0)    # vermelho
    time.sleep(0.5)  # pausa de 100ms entre cada LED
    strip[1] = (0, 255, 0)    # verde
    time.sleep(0.5)  # pausa de 100ms entre cada LED
    strip[8] = (0, 0, 255)    # azul
    time.sleep(0.5)  # pausa de 100ms entre cada LED
    strip[9] = (255, 255, 0)  # amarelo
    strip.write()
    print("LEDs atualizados com sucesso!")

print("Teste básico concluído.")

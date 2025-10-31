import time
# REMOVA as linhas os.environ para permitir a inicialização genérica!

# Importe o objeto 'Pin' genérico
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import neopixel

# --- Configurações ---
# Nós sabemos que este pino funciona graças ao seu teste com blink.py!
PIXEL_PIN = Pin((1, 10)) 
PIXEL_COUNT = 64
BRIGHTNESS = 0.05

# --- Inicialização ---
print("Inicializando NeoPixel no modo genérico Linux...")
print(f"Pino a ser usado: (chip=1, linha=10)")

try:
    strip = neopixel.NeoPixel(
        PIXEL_PIN,
        PIXEL_COUNT,
        brightness=BRIGHTNESS,
        auto_write=False,
        pixel_order=neopixel.GRB
    )
    print("✅ Sucesso! NeoPixel inicializado.")

    # --- Execução do Teste ---
    print("Iniciando animação de teste...")
    while True:
        # Acende alguns LEDs
        print("Acendendo LEDs com cores...")
        strip[0] = (255, 0, 0)  # Vermelho
        strip[1] = (0, 255, 0)  # Verde
        strip[8] = (0, 0, 255)  # Azul
        strip.write()
        time.sleep(1.5)
        
        # Apaga os LEDs
        print("Apagando LEDs...")
        strip.fill((0, 0, 0))
        strip.write()
        time.sleep(1.5)

except Exception as e:
    print(f"\n❌ ERRO AO INICIALIZAR NEOPIXEL: {e}")
    print("\nIsso pode acontecer se a biblioteca NeoPixel genérica ainda tiver problemas.")
    print("Verifique se está executando com 'sudo'.")

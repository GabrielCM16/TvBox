import time
# Nenhuma linha 'os.environ' aqui!
from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
import neopixel # Este 'import' agora vai usar o nosso hack

# --- Configurações ---
PIXEL_PIN = Pin((1, 10))  # Sabemos que este pino funciona
PIXEL_COUNT = 64
BRIGHTNESS = 0.05

# --- Inicialização ---
print("Tentando inicializar com o driver libgpiod 'hackeado'...")

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
        print("Acendendo LEDs (Vermelho)...")
        strip[0] = (255, 0, 0)
        strip[1] = (255, 0, 0)
        strip.write()
        time.sleep(1.5)
        
        print("Acendendo LEDs (Verde)...")
        strip[0] = (0, 255, 0)
        strip[1] = (0, 255, 0)
        strip.write()
        time.sleep(1.5)

except Exception as e:
    print(f"\n❌ ERRO AO INICIALIZAR NEOPIXEL: {e}")

import os
import time

# --- HACK A: A "MENTIRA" ---
# Nós precisamos disso para fazer o 'import board' funcionar sem travar.
os.environ["BLINKA_FORCEBOARD"] = "ROC-RK3328-CC"
os.environ["BLINKA_FORCECHIP"] = "RK3328"

print("Ambiente 'mentindo' para o Blinka (isso é bom)...")

# Agora as importações devem funcionar
try:
    from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
    import neopixel
    print("Importações bem-sucedidas!")
except Exception as e:
    print(f"ERRO NA IMPORTAÇÃO: {e}")
    print("Isso não deveria acontecer se o Hack A funcionou.")
    exit()

# --- HACK B: A "EXPECTATIVA" ---
# O código abaixo assume que você aplicou o hack no arquivo
# /usr/local/lib/python3.7/dist-packages/neopixel_write.py
# (ou similar), onde você comentou o 'raise' e descomentou
# a linha do 'libgpiod_neopixel'.

# --- Configurações ---
PIXEL_PIN = Pin((1, 10))  # Sabemos que este pino funciona
PIXEL_COUNT = 64
BRIGHTNESS = 0.05

# --- Inicialização ---
print("Tentando inicializar NeoPixel com o 'Hack B'...")

try:
    strip = neopixel.NeoPixel(
        PIXEL_PIN,
        PIXEL_COUNT,
        brightness=BRIGHTNESS,
        auto_write=False,
        pixel_order=neopixel.GRB
    )
    print("✅✅✅ SUCESSO! NeoPixel inicializado!")
    print("Se você leu isso, o 'Hack Duplo' funcionou.")

    # --- Execução do Teste ---
    print("Iniciando animação de teste...")
    while True:
        print("Acendendo LEDs (Vermelho)...")
        strip.fill((255, 0, 0))
        strip.write()
        time.sleep(1.5)
        
        print("Acendendo LEDs (Verde)...")
        strip.fill((0, 255, 0))
        strip.write()
        time.sleep(1.5)

except Exception as e:
    print(f"\n❌ ERRO AO INICIALIZAR NEOPIXEL: {e}")
    print("Causa provável: O 'Hack B' (no arquivo da biblioteca) falhou ou não está correto.")
    print("Verifique se você salvou o arquivo da biblioteca.")

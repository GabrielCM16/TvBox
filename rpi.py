import time
# Note: Não estamos mais importando 'neopixel' ou 'board' da Adafruit!
# Estamos usando a biblioteca de baixo nível diretamente.
from rpi_ws281x import Adafruit_NeoPixel, Color

# --- CONFIGURAÇÕES PRINCIPAIS ---
LED_COUNT      = 64       # Total de LEDs na sua matriz 8x8
# Este é o pino que FUNCIONA! A sua fórmula (1, 10) -> 32*1 + 10 = 42
LED_PIN        = 42       
LED_FREQ_HZ    = 800000   # Frequência padrão para NeoPixels
LED_DMA        = 10       # Canal DMA a ser usado (10 é um bom padrão)
LED_BRIGHTNESS = 30       # Brilho (0 a 255). Comece baixo!
LED_INVERT     = False    # Geralmente False

# --- PROGRAMA ---

# Crie o objeto da fita de LED.
strip = Adafruit_NeoPixel(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS
)
# Inicializa a biblioteca (isso é obrigatório).
strip.begin()

print('Iniciando teste. Pressione Ctrl-C para sair.')
try:
    while True:
        print("Definindo cor Vermelha...")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show()
        time.sleep(2)

        print("Definindo cor Verde...")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 255, 0))
        strip.show()
        time.sleep(2)

        print("Definindo cor Azul...")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 255))
        strip.show()
        time.sleep(2)

except KeyboardInterrupt:
    # Este bloco será executado quando você pressionar Ctrl-C
    print("\nDesligando os LEDs.")
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

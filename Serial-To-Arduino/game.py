import serial
import serial.tools.list_ports
import time
import sys
import msvcrt  # leitura de tecla sem Enter (Windows)

# =========================
# CONFIGURAÇÕES
# =========================

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

# Cores (RRRGGGBBB + Intensidade)
COR_JOGADOR = "0002550009"   # verde
COR_FIXO    = "2550000009"   # vermelho

# =========================
# DETECÇÃO DO ARDUINO
# =========================

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        dev = p.device.lower()
        desc = (p.description or "").lower()
        if "acm" in dev or "arduino" in desc or "cdc" in desc:
            return p.device
    return None

porta = detectar_arduino()

if not porta:
    print("[ERRO] Arduino não encontrado")
    sys.exit(1)

print(f"[OK] Arduino detectado em {porta}")

ser = serial.Serial(porta, 9600, timeout=0.05)
time.sleep(2)

# =========================
# FUNÇÕES DE LED
# =========================

def apagar_led(l, c):
    ser.write(f"{l}{c}\n".encode())

def acender_led(l, c, cor):
    ser.write(f"{l}{c}{cor}\n".encode())

def ler_retorno():
    while ser.in_waiting:
        resp = ser.readline().decode(errors="ignore").strip()
        if resp:
            print(f"[ARDUINO] {resp}")

# =========================
# INICIALIZAÇÃO VISUAL
# =========================

ser.write(b"CL\n")
time.sleep(0.05)

# LEDs fixos
acender_led(5, 5, COR_FIXO)
acender_led(7, 7, COR_FIXO)

# Jogador
linha = 0
coluna = 0
acender_led(linha, coluna, COR_JOGADOR)

print("\n=== JOGO MATRIZ LED ===")
print("W A S D -> mover | Q -> sair")
print("======================\n")

# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:

        # leitura serial contínua
        ler_retorno()

        if msvcrt.kbhit():
            tecla = msvcrt.getch().decode("utf-8").upper()

            if tecla == "Q":
                break

            nova_linha = linha
            nova_coluna = coluna

            if tecla == "W":
                nova_linha -= 1
            elif tecla == "S":
                nova_linha += 1
            elif tecla == "A":
                nova_coluna -= 1
            elif tecla == "D":
                nova_coluna += 1
            else:
                continue

            # valida limites
            if not (0 <= nova_linha < MATRIZ_LINHAS and 0 <= nova_coluna < MATRIZ_COLUNAS):
                continue

            # atualiza posição
            apagar_led(linha, coluna)
            linha, coluna = nova_linha, nova_coluna
            acender_led(linha, coluna, COR_JOGADOR)

        time.sleep(0.01)

except KeyboardInterrupt:
    pass

finally:
    ser.close()
    print("\n[INFO] Conexão encerrada")

import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios
import random

# =========================
# CONFIGURAÇÕES
# =========================

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

# Cores (RRRGGGBBB + I)
COR_JOGADOR     = "0002550001"  # verde
COR_FIXO        = "2550000001"  # vermelho
COR_SELECIONADO = "0000002551"  # azul
COR_VITORIA     = "2552552551"  # branco

QTD_PARES = 4

# =========================
# TECLADO (LINUX)
# =========================

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# =========================
# DETECÇÃO DO ARDUINO
# =========================

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        d = p.device.lower()
        desc = (p.description or "").lower()
        if "acm" in d or "arduino" in desc or "cdc" in desc:
            return p.device
    return None

porta = detectar_arduino() or "/dev/ttyS2"

print(f"[OK] Porta serial: {porta}")

ser = serial.Serial(porta, 115200, timeout=0.05, write_timeout=0.05, exclusive=True)
time.sleep(2)

# =========================
# LEDS
# =========================

def apagar_led(l, c):
    ser.write(f"{l}{c}\n".encode())
    ser.flush()

def acender_led(l, c, cor):
    ser.write(f"{l}{c}{cor}\n".encode())
    ser.flush()

def limpar_matriz():
    ser.write(b"CL\n")
    ser.flush()

# =========================
# LÓGICA DO JOGO
# =========================

def sortear_pares(qtd):
    total = MATRIZ_LINHAS * MATRIZ_COLUNAS
    pos = random.sample(range(total), qtd * 2)
    pares = set()

    for p in pos:
        l = p // MATRIZ_COLUNAS
        c = p % MATRIZ_COLUNAS
        pares.add((l, c))
        acender_led(l, c, COR_FIXO)

    return pares

def animacao_vitoria():
    for _ in range(3):
        limpar_matriz()
        time.sleep(0.15)
        for l in range(MATRIZ_LINHAS):
            for c in range(MATRIZ_COLUNAS):
                acender_led(l, c, COR_VITORIA)
        time.sleep(0.2)

    limpar_matriz()

    for l in range(MATRIZ_LINHAS):
        for c in range(MATRIZ_COLUNAS):
            acender_led(l, c, COR_FIXO)
            time.sleep(0.01)

# =========================
# INICIALIZAÇÃO
# =========================

print("\n=== JOGO MATRIZ LED ===")
print("W A S D -> mover | X -> selecionar | Q -> sair\n")

limpar_matriz()

leds_fixos = sortear_pares(QTD_PARES)
selecionados = set()

linha, coluna = 0, 0
acender_led(linha, coluna, COR_JOGADOR)

# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:
        cmd = getch().upper()

        if cmd == "Q":
            break

        if cmd == "X":
            if (linha, coluna) in leds_fixos:
                selecionados.add((linha, coluna))
                acender_led(linha, coluna, COR_SELECIONADO)

                if selecionados == leds_fixos:
                    animacao_vitoria()
                    break
            continue

        nl, nc = linha, coluna

        if cmd == "W": nl -= 1
        elif cmd == "S": nl += 1
        elif cmd == "A": nc -= 1
        elif cmd == "D": nc += 1
        else:
            continue

        if not (0 <= nl < MATRIZ_LINHAS and 0 <= nc < MATRIZ_COLUNAS):
            continue

        if (linha, coluna) not in selecionados:
            apagar_led(linha, coluna)

        linha, coluna = nl, nc

        if (linha, coluna) in selecionados:
            acender_led(linha, coluna, COR_SELECIONADO)
        elif (linha, coluna) in leds_fixos:
            acender_led(linha, coluna, COR_FIXO)
        else:
            acender_led(linha, coluna, COR_JOGADOR)

        time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    limpar_matriz()
    ser.close()
    print("[INFO] Jogo encerrado")

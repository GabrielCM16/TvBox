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

COR_JOGADOR     = "0002550001"  # verde
COR_MEMORIA     = "2550000001"  # vermelho
COR_SELECIONADO = "0000002551"  # azul
COR_DERROTA     = "2551280001"  # laranja
COR_VITORIA     = "2552552551"  # branco

QTD_LEDS_MEMORIA = 6
MAX_ERROS = 3

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
# ARDUINO
# =========================

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        dev = p.device.lower()
        desc = (p.description or "").lower()
        if "acm" in dev or "arduino" in desc or "cdc" in desc:
            return p.device
    return None

porta = detectar_arduino() or "/dev/ttyS2"
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
# ANIMAÇÕES
# =========================

def animacao_derrota():
    for _ in range(2):
        for l in range(MATRIZ_LINHAS):
            for c in range(MATRIZ_COLUNAS):
                acender_led(l, c, COR_DERROTA)
        time.sleep(0.2)
        limpar_matriz()
        time.sleep(0.15)

def animacao_game_over():
    for _ in range(3):
        for l in range(MATRIZ_LINHAS):
            for c in range(MATRIZ_COLUNAS):
                acender_led(l, c, COR_DERROTA)
        time.sleep(0.3)
        limpar_matriz()
        time.sleep(0.2)

def animacao_vitoria():
    for _ in range(3):
        limpar_matriz()
        time.sleep(0.15)
        for l in range(MATRIZ_LINHAS):
            for c in range(MATRIZ_COLUNAS):
                acender_led(l, c, COR_VITORIA)
        time.sleep(0.2)
    limpar_matriz()

# =========================
# JOGO
# =========================

def sortear_leds(qtd):
    total = MATRIZ_LINHAS * MATRIZ_COLUNAS
    posicoes = random.sample(range(total), qtd)
    leds = set()

    for p in posicoes:
        l = p // MATRIZ_COLUNAS
        c = p % MATRIZ_COLUNAS
        leds.add((l, c))
        acender_led(l, c, COR_MEMORIA)

    return leds

def mostrar_memoria(leds):
    limpar_matriz()
    for (l, c) in leds:
        acender_led(l, c, COR_MEMORIA)

# =========================
# INICIALIZAÇÃO
# =========================

print("\n=== JOGO MATRIZ LED ===")
print("Memorize os LEDs")
print("W A S D mover | X marcar | Q sair\n")

limpar_matriz()

leds_memoria = sortear_leds(QTD_LEDS_MEMORIA)

erros_totais = 0

# =========================
# LOOP DE RODADAS
# =========================

while True:
    selecionados = set()
    jogo_iniciado = False

    linha, coluna = 0, 0
    acender_led(linha, coluna, COR_JOGADOR)

    try:
        while True:
            cmd = getch().upper()

            if cmd == "Q":
                raise KeyboardInterrupt

            if not jogo_iniciado and cmd in ("W", "A", "S", "D"):
                limpar_matriz()
                acender_led(linha, coluna, COR_JOGADOR)
                jogo_iniciado = True

            if cmd == "X":
                if (linha, coluna) not in selecionados:
                    selecionados.add((linha, coluna))
                    acender_led(linha, coluna, COR_SELECIONADO)

                    # ERRO
                    if (linha, coluna) not in leds_memoria:
                        erros_totais += 1
                        animacao_derrota()

                        if erros_totais >= MAX_ERROS:
                            animacao_game_over()
                            raise KeyboardInterrupt

                        mostrar_memoria(leds_memoria)
                        time.sleep(1)
                        break  # reinicia rodada

                    # VITÓRIA
                    if selecionados == leds_memoria:
                        animacao_vitoria()
                        raise KeyboardInterrupt
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
            else:
                acender_led(linha, coluna, COR_JOGADOR)

            time.sleep(0.02)

    except KeyboardInterrupt:
        break

# =========================
# FINALIZAÇÃO
# =========================

limpar_matriz()
ser.close()
print("[INFO] Jogo encerrado")

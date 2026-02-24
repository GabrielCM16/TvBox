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

QTD_LEDS_MEMORIA = 2
MAX_ERROS = 3

# =========================
# FUNÇÕES DE APOIO
# =========================
def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        dev = p.device.lower()
        if "/dev/ttyacm" in dev or "/dev/ttyusb" in dev:
            return p.device
    return None

porta = detectar_arduino()

if not porta:
    print("[ERRO] Arduino não encontrado \n-- Usando porta padrão")
    porta = "/dev/ttyS2" # portas rx tx da placa da tv box
    #sys.exit(1)

print(f"[OK] Arduino detectado em {porta}")

ser = serial.Serial(porta, 115200, timeout=0.05, write_timeout=0.05, exclusive=True)
time.sleep(2)

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
        time.sleep(0.15)
        limpar_matriz()
        time.sleep(0.1)

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
# LÓGICA DE JOGO
# =========================
print("\n=== JOGO MATRIZ LED (MODO RESET) ===")
print("W A S D mover | ENTER marcar | P pausar\n")

# Sorteio inicial
limpar_matriz()
posicoes = random.sample(range(MATRIZ_LINHAS * MATRIZ_COLUNAS), QTD_LEDS_MEMORIA)
leds_memoria = {(p // MATRIZ_COLUNAS, p % MATRIZ_COLUNAS) for p in posicoes}

acertos = set()
erros_totais = 0
linha, coluna = 0, 0
jogo_iniciado = False

# Mostra memória inicial
for (l, c) in leds_memoria:
    acender_led(l, c, COR_MEMORIA)
acender_led(linha, coluna, COR_JOGADOR)

try:
    while True:
        cmd = getch().upper()

        if cmd in ("\r", "\n"):
            cmd = "ENTER"

        if cmd == "P": break

        # Começou a jogar: apaga a memória
        if not jogo_iniciado and cmd in ("W", "A", "S", "D", "ENTER"):
            limpar_matriz()
            acender_led(linha, coluna, COR_JOGADOR)
            jogo_iniciado = True

        if cmd == "ENTER":
            if (linha, coluna) in leds_memoria:
                if (linha, coluna) not in acertos:
                    acertos.add((linha, coluna))
                    acender_led(linha, coluna, COR_SELECIONADO)
                    
                    # Vitória: acertou todos os sorteados
                    if acertos == leds_memoria:
                        animacao_vitoria()
                        break
            else:
                # ERROU: Reset Total
                erros_totais += 1
                animacao_derrota()
                
                if erros_totais >= MAX_ERROS:
                    print("GAME OVER!")
                    animacao_game_over()
                    break
                
                print(f"Erro {erros_totais}/{MAX_ERROS}! Resetando...")
                # Reseta o progresso da rodada
                acertos.clear()
                linha, coluna = 0, 0
                jogo_iniciado = False
                
                # Mostra tudo de novo para o jogador decorar
                limpar_matriz()
                for (l, c) in leds_memoria:
                    acender_led(l, c, COR_MEMORIA)
                acender_led(linha, coluna, COR_JOGADOR)
            continue

        # MOVIMENTAÇÃO
        nl, nc = linha, coluna
        if cmd == "W": nl -= 1
        elif cmd == "S": nl += 1
        elif cmd == "A": nc -= 1
        elif cmd == "D": nc += 1
        else: continue

        if 0 <= nl < MATRIZ_LINHAS and 0 <= nc < MATRIZ_COLUNAS:
            # Apaga onde o jogador estava (se não era um acerto azul)
            if (linha, coluna) not in acertos:
                apagar_led(linha, coluna)
            else:
                acender_led(linha, coluna, COR_SELECIONADO)

            linha, coluna = nl, nc
            # Mostra o jogador na nova posição
            acender_led(linha, coluna, COR_JOGADOR)

        time.sleep(0.01)

except KeyboardInterrupt:
    pass

limpar_matriz()
ser.close()
print("[INFO] Jogo encerrado")
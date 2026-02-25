import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios
import random

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

# Formato: "RRRGGGBBB1" (3 dígitos por canal)
COR_JOGADOR     = "0002550001"  # verde
COR_MEMORIA     = "2550000001"  # vermelho
COR_SELECIONADO = "0000002551"  # azul
COR_X           = "2550000001"  # vermelho (X)
COR_APAGADO     = None

MAX_ERROS = 3

# pacing para TV Box / USB serial
USB_PACING = 0.004

# Cores para animações (vitoria "colorida")
PALETA = [
    "2550000001",  # vermelho
    "2551280001",  # laranja
    "2552550001",  # amarelo
    "0002550001",  # verde
    "0002552551",  # ciano
    "0000002551",  # azul
    "1280002551",  # roxo
    "2550002551",  # magenta
    "2552552551",  # branco
]

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def read_key():
    """
    Normaliza teclado:
    - WASD
    - ENTER
    - P
    - Setas (ESC [ A/B/C/D) => UP/DOWN/RIGHT/LEFT
    Retorna: "W","A","S","D","ENTER","P","UP","DOWN","LEFT","RIGHT" ou "".
    """
    ch = getch()
    if ch in ("\r", "\n"):
        return "ENTER"

    # Sequência de escape das setas
    if ch == "\x1b":  # ESC
        ch2 = getch()  # normalmente '['
        if ch2 == "[":
            ch3 = getch()  # A/B/C/D
            if ch3 == "A":
                return "UP"
            if ch3 == "B":
                return "DOWN"
            if ch3 == "C":
                return "RIGHT"
            if ch3 == "D":
                return "LEFT"
        return ""

    return ch.upper()

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        if "ACM" in p.device or "USB" in p.device:
            return p.device
    return "/dev/ttyACM0"

porta = detectar_arduino()
print("[PORTA]", porta)

ser = serial.Serial(
    porta,
    115200,
    timeout=1,
    write_timeout=2,   # um pouco mais folgado
    rtscts=False,
    dsrdtr=False
)
time.sleep(3)
ser.reset_input_buffer()

# aguarda READY
t0 = time.time()
while time.time() - t0 < 4:
    r = ser.readline().decode(errors="ignore").strip()
    if r:
        print("[ARDUINO]", r)
        if "READY" in r:
            break

# ---------- SERIAL SAFE ----------
def enviar(cmd, retries=3):
    data = (cmd + "\n").encode()
    for i in range(retries):
        try:
            ser.write(data)
            ser.flush()
            time.sleep(USB_PACING)
            return True
        except serial.SerialTimeoutException:
            # tenta destravar buffer e repetir
            try:
                ser.reset_output_buffer()
            except Exception:
                pass
            time.sleep(0.03 * (i + 1))
        except Exception:
            # falha genérica: não derruba o jogo durante animação
            time.sleep(0.02)
    return False

def apagar_led(l, c):
    enviar(f"{l}{c}")

def acender_led(l, c, cor):
    enviar(f"{l}{c}{cor}")

def limpar_matriz():
    enviar("CL")

# ---------- ANIMAÇÕES ----------
def preencher(cor):
    for l in range(MATRIZ_LINHAS):
        for c in range(MATRIZ_COLUNAS):
            acender_led(l, c, cor)

def desenhar_X(cor):
    # X nas diagonais
    limpar_matriz()
    for i in range(8):
        acender_led(i, i, cor)
        acender_led(i, 7 - i, cor)

def animacao_derrota_X():
    # X vermelho piscando
    for _ in range(3):
        desenhar_X(COR_X)
        time.sleep(0.18)
        limpar_matriz()
        time.sleep(0.10)
    desenhar_X(COR_X)
    time.sleep(0.22)
    limpar_matriz()

def animacao_vitoria_colorida():
    # varredura colorida + flash
    for cor in PALETA[:7]:
        preencher(cor)
        time.sleep(0.08)
        limpar_matriz()
        time.sleep(0.03)
    for _ in range(2):
        preencher("2552552551")
        time.sleep(0.08)
        limpar_matriz()
        time.sleep(0.06)

def animacao_round_start(qtd):
    # “carregando” discreto: barra na primeira linha com cores alternadas
    limpar_matriz()
    cor = PALETA[qtd % len(PALETA)]
    for c in range(min(qtd, 8)):
        acender_led(0, c, cor)
        time.sleep(0.03)
    time.sleep(0.10)
    limpar_matriz()

# ---------- JOGO (ROUND) ----------
def novo_round(qtd_leds):
    qtd_leds = max(2, min(64, qtd_leds))
    posicoes = random.sample(range(64), qtd_leds)
    leds_memoria = {(p // 8, p % 8) for p in posicoes}
    return leds_memoria

def loop_round(leds_memoria):
    """
    Executa 1 round.
    Retorna: True (ganhou) / False (perdeu por erros)
    """
    acertos = set()
    erros_totais = 0
    linha, coluna = 0, 0
    jogo_iniciado = False

    # mostra memória
    for l, c in leds_memoria:
        acender_led(l, c, COR_MEMORIA)

    acender_led(linha, coluna, COR_JOGADOR)

    while True:
        k = read_key()
        if not k:
            continue

        if k == "P":
            return None  # sinaliza saída total

        # mapeia setas para WASD (ordem padrão)
        if k == "UP":
            k = "W"
        elif k == "DOWN":
            k = "S"
        elif k == "LEFT":
            k = "A"
        elif k == "RIGHT":
            k = "D"

        # primeira ação apaga memória
        if not jogo_iniciado and k in ("W", "A", "S", "D", "ENTER"):
            limpar_matriz()
            acender_led(linha, coluna, COR_JOGADOR)
            jogo_iniciado = True

        # seleção
        if k == "ENTER":
            if (linha, coluna) in leds_memoria:
                if (linha, coluna) not in acertos:
                    acertos.add((linha, coluna))
                    acender_led(linha, coluna, COR_SELECIONADO)

                if acertos == leds_memoria:
                    return True
            else:
                erros_totais += 1

                # feedback rápido de erro
                animacao_derrota_X()

                if erros_totais >= MAX_ERROS:
                    return False

                # reseta tentativa do round (mantém mesma memória)
                acertos.clear()
                linha, coluna = 0, 0
                jogo_iniciado = False

                limpar_matriz()
                for l, c in leds_memoria:
                    acender_led(l, c, COR_MEMORIA)
                acender_led(linha, coluna, COR_JOGADOR)
            continue

        # movimento (com A/D invertidos)
        nl, nc = linha, coluna
        if k == "W":
            nl -= 1
        elif k == "S":
            nl += 1
        elif k == "A":
            # INVERTIDO: A agora vai pra direita
            nc += 1
        elif k == "D":
            # INVERTIDO: D agora vai pra esquerda
            nc -= 1
        else:
            continue

        if 0 <= nl < 8 and 0 <= nc < 8:
            # restaura pixel anterior
            if (linha, coluna) not in acertos:
                apagar_led(linha, coluna)
            else:
                acender_led(linha, coluna, COR_SELECIONADO)

            linha, coluna = nl, nc
            acender_led(linha, coluna, COR_JOGADOR)

# ---------- MAIN ----------
print("\n=== JOGO MATRIZ LED (LEVELS) ===")
print("WASD mover (A/D invertidos) | Setas também | ENTER marcar | P sair\n")

limpar_matriz()

nivel_leds = 2

try:
    while True:
        animacao_round_start(nivel_leds)

        leds_memoria = novo_round(nivel_leds)
        resultado = loop_round(leds_memoria)

        if resultado is None:
            break  # P

        if resultado is True:
            animacao_vitoria_colorida()
            nivel_leds = min(64, nivel_leds + 1)
            print(f"[OK] Vitória. Próximo nível: {nivel_leds} LEDs")
        else:
            # perdeu por erros
            # X vermelho já é mostrado nos erros; aqui reforça “game over” visual
            desenhar_X(COR_X)
            time.sleep(0.35)
            limpar_matriz()

            nivel_leds = 2
            print("[KO] Game Over. Reset para 2 LEDs")

except KeyboardInterrupt:
    pass
finally:
    try:
        limpar_matriz()
    except Exception:
        pass
    try:
        ser.close()
    except Exception:
        pass
    print("[INFO] encerrado")
import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios
import random

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

COR_JOGADOR     = "0002550001"  # verde
COR_MEMORIA     = "2550000001"  # vermelho
COR_SELECIONADO = "0000002551"  # azul
COR_X           = "2550000001"  # vermelho

MAX_ERROS = 3
USB_PACING = 0.004

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def read_key():
    ch = getch()
    if ch in ("\r", "\n"):
        return "ENTER"

    if ch == "\x1b":  # ESC
        ch2 = getch()
        if ch2 == "[":
            ch3 = getch()
            if ch3 == "A": return "UP"
            if ch3 == "B": return "DOWN"
            if ch3 == "C": return "RIGHT"
            if ch3 == "D": return "LEFT"
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
    porta, 115200,
    timeout=1,
    write_timeout=2,
    rtscts=False,
    dsrdtr=False
)
time.sleep(3)
ser.reset_input_buffer()

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
            try:
                ser.reset_output_buffer()
            except Exception:
                pass
            time.sleep(0.04 * (i + 1))
        except Exception:
            time.sleep(0.03)
    return False

def apagar_led(l, c):
    enviar(f"{l}{c}")

def acender_led(l, c, cor):
    enviar(f"{l}{c}{cor}")

def limpar_matriz():
    enviar("CL")

# ---------- ANIMAÇÕES ----------
def desenhar_X(cor):
    limpar_matriz()
    for i in range(8):
        acender_led(i, i, cor)
        acender_led(i, 7 - i, cor)

def animacao_derrota_X():
    for _ in range(3):
        desenhar_X(COR_X)
        time.sleep(0.18)
        limpar_matriz()
        time.sleep(0.10)
    desenhar_X(COR_X)
    time.sleep(0.22)
    limpar_matriz()

def desenhar_check_verde():
    """
    ✔ corrigido (espelhamento esq/dir): col = 7 - col
    Poucos pixels (leve no serial).
    """
    limpar_matriz()
    pts = [
        (5,1),(6,2),
        (6,3),(5,4),
        (4,5),(3,6),(2,7)
    ]
    for l, c in pts:
        c = 7 - c  # <-- ESPELHA HORIZONTAL (corrige “ao contrário”)
        acender_led(l, c, COR_JOGADOR)

def animacao_vitoria_lenta_verde():
    # estilo do X: poucos frames, sem nada rápido
    desenhar_check_verde()
    time.sleep(0.22)
    limpar_matriz()
    time.sleep(0.12)
    desenhar_check_verde()
    time.sleep(0.22)
    limpar_matriz()

def animacao_round_start(qtd):
    # leve e lenta (sem loop com sleeps curtos)
    limpar_matriz()
    # mostra só 3 LEDs no topo como “nível”
    limite = min(qtd, 3)
    for c in range(limite):
        acender_led(0, c, COR_JOGADOR)
    time.sleep(0.18)
    limpar_matriz()

# ---------- MEMÓRIA (CRESCENTE) ----------
def memoria_inicial(qtd):
    qtd = max(2, min(64, qtd))
    pos = random.sample(range(64), qtd)
    return {(p // 8, p % 8) for p in pos}

def memoria_adicionar_um(leds_memoria):
    # adiciona 1 posição nova sem mexer nas antigas
    if len(leds_memoria) >= 64:
        return leds_memoria
    livres = [(l, c) for l in range(8) for c in range(8) if (l, c) not in leds_memoria]
    novo = random.choice(livres)
    leds_memoria.add(novo)
    return leds_memoria

# ---------- JOGO (ROUND) ----------
def loop_round(leds_memoria):
    """
    Executa 1 round com a memória atual.
    Retorna:
      True  -> ganhou
      False -> perdeu (MAX_ERROS)
      None  -> saiu (P)
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
            return None

        # setas -> WASD
        if k == "UP": k = "W"
        elif k == "DOWN": k = "S"
        elif k == "LEFT": k = "A"
        elif k == "RIGHT": k = "D"

        # primeira ação apaga memória
        if not jogo_iniciado and k in ("W", "A", "S", "D", "ENTER"):
            limpar_matriz()
            acender_led(linha, coluna, COR_JOGADOR)
            jogo_iniciado = True

        # ENTER marca
        if k == "ENTER":
            if (linha, coluna) in leds_memoria:
                if (linha, coluna) not in acertos:
                    acertos.add((linha, coluna))
                    acender_led(linha, coluna, COR_SELECIONADO)

                if acertos == leds_memoria:
                    return True
            else:
                erros_totais += 1
                animacao_derrota_X()

                if erros_totais >= MAX_ERROS:
                    return False

                # reseta tentativa do round (mesma memória)
                acertos.clear()
                linha, coluna = 0, 0
                jogo_iniciado = False

                limpar_matriz()
                for l, c in leds_memoria:
                    acender_led(l, c, COR_MEMORIA)
                acender_led(linha, coluna, COR_JOGADOR)
            continue

        # movimento (A/D invertidos)
        nl, nc = linha, coluna
        if k == "W": nl -= 1
        elif k == "S": nl += 1
        elif k == "A": nc += 1   # A -> direita
        elif k == "D": nc -= 1   # D -> esquerda
        else:
            continue

        if 0 <= nl < 8 and 0 <= nc < 8:
            if (linha, coluna) not in acertos:
                apagar_led(linha, coluna)
            else:
                acender_led(linha, coluna, COR_SELECIONADO)

            linha, coluna = nl, nc
            acender_led(linha, coluna, COR_JOGADOR)

# ---------- MAIN ----------
print("\n=== JOGO MATRIZ LED (MEMÓRIA CRESCENTE) ===")
print("WASD mover (A/D invertidos) | Setas também | ENTER marcar | P sair\n")

limpar_matriz()

leds_memoria = memoria_inicial(2)

try:
    while True:
        animacao_round_start(len(leds_memoria))

        resultado = loop_round(leds_memoria)

        if resultado is None:
            break

        if resultado is True:
            animacao_vitoria_lenta_verde()
            memoria_adicionar_um(leds_memoria)  # adiciona +1 sem mexer nos antigos
            print(f"[OK] Vitória. Memória agora: {len(leds_memoria)} LEDs")
        else:
            # perdeu -> reseta para 2 (com posições novas)
            desenhar_X(COR_X)
            time.sleep(0.30)
            limpar_matriz()

            leds_memoria = memoria_inicial(2)
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
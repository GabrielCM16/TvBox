import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios
import random
import select

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

COR_JOGADOR     = "0002550001"  # verde
COR_MEMORIA     = "2550000001"  # vermelho
COR_SELECIONADO = "0000002551"  # azul
COR_X           = "2550000001"  # vermelho

MAX_ERROS = 3

# pacing base + adaptativo (anti travamento)
USB_PACING_BASE = 0.004
USB_PACING_MAX  = 0.020
usb_pacing = USB_PACING_BASE

# heurística de “link degradado”
timeout_streak = 0
TIMEOUT_STREAK_RECONNECT = 10  # reconecta após N timeouts seguidos

# ---------- TECLADO ----------
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

def drenar_teclado():
    """
    Remove teclas “acumuladas” quando o jogo ficou lento.
    Não bloqueia.
    """
    try:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if not r:
                    break
                sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        pass

# ---------- SERIAL ----------
def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        if "ACM" in p.device or "USB" in p.device:
            return p.device
    return "/dev/ttyACM0"

porta = detectar_arduino()
print("[PORTA]", porta)

def abrir_serial():
    s = serial.Serial(
        porta, 115200,
        timeout=1,
        write_timeout=2,
        rtscts=False,
        dsrdtr=False
    )
    time.sleep(2.5)
    try:
        s.reset_input_buffer()
        s.reset_output_buffer()
    except Exception:
        pass
    return s

ser = abrir_serial()

# tenta ler READY (sem depender disso 100%)
t0 = time.time()
while time.time() - t0 < 3.5:
    try:
        r = ser.readline().decode(errors="ignore").strip()
        if r:
            print("[ARDUINO]", r)
            if "READY" in r:
                break
    except Exception:
        break

def drenar_serial(max_bytes=4096):
    """
    Evita acumular lixo/prints do Arduino no buffer.
    """
    try:
        n = ser.in_waiting
        if n:
            ser.read(min(n, max_bytes))
    except Exception:
        pass

def tentar_reconectar():
    """
    Recuperação automática sem reiniciar o jogo.
    """
    global ser, timeout_streak, usb_pacing
    try:
        print("[WARN] Reconectando serial...")
        try:
            ser.close()
        except Exception:
            pass
        time.sleep(0.4)
        ser = abrir_serial()
        timeout_streak = 0
        usb_pacing = min(USB_PACING_MAX, USB_PACING_BASE + 0.006)

        # drena qualquer lixo inicial
        t0 = time.time()
        while time.time() - t0 < 1.0:
            drenar_serial()
            time.sleep(0.05)

        print("[OK] Serial reconectada.")
        return True
    except Exception as e:
        print("[ERRO] Falha ao reconectar:", e)
        return False

# ---------- SERIAL SAFE ----------
def enviar(cmd, retries=3):
    """
    Envio robusto:
    - pacing adaptativo
    - drena buffer
    - retry com backoff
    - auto-reconnect ao detectar sequência de timeouts
    """
    global usb_pacing, timeout_streak

    drenar_serial()

    data = (cmd + "\n").encode()
    for i in range(retries):
        try:
            ser.write(data)
            ser.flush()
            time.sleep(usb_pacing)

            # sucesso -> reduz pacing gradualmente
            if usb_pacing > USB_PACING_BASE:
                usb_pacing = max(USB_PACING_BASE, usb_pacing - 0.001)

            timeout_streak = 0
            return True

        except serial.SerialTimeoutException:
            timeout_streak += 1

            # congestionou -> aumenta pacing + backoff
            usb_pacing = min(USB_PACING_MAX, usb_pacing + 0.003)
            try:
                ser.reset_output_buffer()
            except Exception:
                pass

            # se está muito degradado, limpa teclado e espera um pouco
            drenar_teclado()
            time.sleep(0.08 * (i + 1))

            if timeout_streak >= TIMEOUT_STREAK_RECONNECT:
                if tentar_reconectar():
                    # após reconectar, tenta reenviar 1 vez
                    try:
                        ser.write(data)
                        ser.flush()
                        time.sleep(usb_pacing)
                        return True
                    except Exception:
                        return False
                return False

        except Exception:
            timeout_streak += 1
            drenar_teclado()
            time.sleep(0.06)

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
    limpar_matriz()
    pts = [
        (5,1),(6,2),
        (6,3),(5,4),
        (4,5),(3,6),(2,7)
    ]
    for l, c in pts:
        c = 7 - c
        acender_led(l, c, COR_JOGADOR)

def animacao_vitoria_lenta_verde():
    desenhar_check_verde()
    time.sleep(0.24)
    limpar_matriz()
    time.sleep(0.12)
    desenhar_check_verde()
    time.sleep(0.24)
    limpar_matriz()

def animacao_round_start(qtd):
    # leve e lenta (sem loop com sleeps curtos)
    limpar_matriz()
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
    if len(leds_memoria) >= 64:
        return leds_memoria
    livres = [(l, c) for l in range(8) for c in range(8) if (l, c) not in leds_memoria]
    novo = random.choice(livres)
    leds_memoria.add(novo)
    return leds_memoria

# ---------- JOGO (ROUND) ----------
def loop_round(leds_memoria):
    acertos = set()
    erros_totais = 0
    linha, coluna = 0, 0
    jogo_iniciado = False

    # mostra memória
    for l, c in leds_memoria:
        acender_led(l, c, COR_MEMORIA)

    acender_led(linha, coluna, COR_JOGADOR)

    while True:
        # drena “lixo” continuamente para não congestionar
        drenar_serial()

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

                # reseta tentativa (mesma memória)
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
            memoria_adicionar_um(leds_memoria)
            print(f"[OK] Vitória. Memória agora: {len(leds_memoria)} LEDs")
        else:
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
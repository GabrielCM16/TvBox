import serial
import serial.tools.list_ports
import time
import sys
import tty      # Nativo do Linux
import termios  # Nativo do Linux

# =========================
# CONFIGURAÇÕES
# =========================

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

# Cores (RRRGGGBBB + I)
COR_JOGADOR = "0002550001"   # verde
COR_FIXO    = "2550000001"   # vermelho

# =========================
# FUNÇÃO PARA LER TECLA (LINUX)
# =========================

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

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
    print("[ERRO] Arduino não encontrado \n-- Usando porta padrão")
    porta = "/dev/ttyS2" # portas rx tx da placa da tv box
    #sys.exit(1)

print(f"[OK] Arduino detectado em {porta}")

ser = serial.Serial(
    porta,
    115200,
    timeout=0.05,
    write_timeout=0.05,
    exclusive=True
)


time.sleep(2)

# =========================
# FUNÇÕES DE LED
# =========================

def apagar_led(l, c):
    ser.write(f"{l}{c}\n".encode())
    ser.flush()

def acender_led(l, c, cor):
    ser.write(f"{l}{c}{cor}\n".encode())
    ser.flush()


def ler_retorno():
    while ser.in_waiting > 0:
        resp = ser.readline().decode(errors="ignore").strip()
        if resp:
            print(f"[ARDUINO] {resp}")


# =========================
# INICIALIZAÇÃO
# =========================

print("\n=== JOGO MATRIZ LED ===")
print("Controle: W A S D (Direto, sem Enter)")
print("Pressione 'Q' para sair")
print("=======================\n")

# Limpa matriz
ser.write(b"CL\n")
ler_retorno()

# LEDs fixos
acender_led(5, 5, COR_FIXO)
acender_led(7, 7, COR_FIXO)
ler_retorno()

# Jogador
linha = 0
coluna = 0
acender_led(linha, coluna, COR_JOGADOR)
ler_retorno()

# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:
        cmd = getch().upper()

        if cmd == "Q" or cmd == "X":
            break

        nova_linha = linha
        nova_coluna = coluna

        if cmd == "W":
            nova_linha -= 1
        elif cmd == "S":
            nova_linha += 1
        elif cmd == "A":
            nova_coluna -= 1
        elif cmd == "D":
            nova_coluna += 1
        else:
            # Ignora qualquer outra tecla silenciosamente
            continue

        # valida limites
        if not (0 <= nova_linha < MATRIZ_LINHAS and 0 <= nova_coluna < MATRIZ_COLUNAS):
            continue

        # atualiza posição
        apagar_led(linha, coluna)
        linha, coluna = nova_linha, nova_coluna
        acender_led(linha, coluna, COR_JOGADOR)

        ler_retorno()
        time.sleep(0.02)  # 20ms


except KeyboardInterrupt:
    pass

finally:
    ser.write(("CL\n").encode())
    ser.close()
    print("\n[INFO] Conexão encerrada")
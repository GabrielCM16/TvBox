import serial
import serial.tools.list_ports
import time
import sys

# =========================
# CONFIGURAÇÕES E CONSTANTES
# =========================

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

# Cores (RRRGGGBBB + Intensidade)
COR_VERMELHO = "2550000009"
COR_VERDE    = "0002550009"
COR_AZUL     = "0000002559"
COR_AMARELO  = "2552550009"
COR_ROXO     = "2550002559"

COR_ATUAL = COR_VERDE  # cor do "jogador"

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

ser = serial.Serial(porta, 9600, timeout=0.1)
time.sleep(2)

# =========================
# ESTADO DO JOGO
# =========================

linha = 0
coluna = 0

def apagar_led(l, c):
    ser.write(f"{l}{c}\n".encode())

def acender_led(l, c, cor):
    ser.write(f"{l}{c}{cor}\n".encode())

# LED inicial
acender_led(linha, coluna, COR_ATUAL)

# =========================
# ONBOARDING
# =========================

print("\n=== JOGO MATRIZ LED ===\n")
print("Controles:")
print("  W -> Cima")
print("  S -> Baixo")
print("  A -> Esquerda")
print("  D -> Direita")
print("  EXIT -> Encerrar\n")

print("Posição inicial: (0, 0)")
print("============================\n")

# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:
        cmd = input(">> ").strip().upper()

        if not cmd:
            continue

        if cmd == "EXIT":
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
            print("[WARN] Comando inválido")
            continue

        # Validação de limites
        if not (0 <= nova_linha < MATRIZ_LINHAS and 0 <= nova_coluna < MATRIZ_COLUNAS):
            print("[INFO] Movimento ignorado (fora da matriz)")
            continue

        # Atualização visual
        apagar_led(linha, coluna)
        linha, coluna = nova_linha, nova_coluna
        acender_led(linha, coluna, COR_ATUAL)

except KeyboardInterrupt:
    pass

finally:
    ser.close()
    print("\n[INFO] Conexão encerrada")

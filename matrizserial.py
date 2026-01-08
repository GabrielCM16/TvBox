import serial
import serial.tools.list_ports
import time
import sys

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

# Onboarding / exemplos
print("\n=== CONTROLE MATRIZ LED ===\n")
print("Comandos disponíveis:")
print("  CL                  -> Limpa toda a matriz")
print("  LC                  -> Desliga LED (linha, coluna)")
print("  LCRRRGGGBBBI        -> Liga LED com cor e intensidade\n")

print("Exemplos:")
print("  23                  -> Desliga LED linha 2 coluna 3")
print("  23025500009         -> LED (2,3) vermelho forte")
print("  45000025504         -> LED (4,5) azul médio")
print("  CL                  -> Limpa tudo")
print("  EXIT                -> Encerra\n")

print("=================================\n")

try:
    while True:
        cmd = input(">> ").strip().upper()

        if not cmd:
            continue

        if cmd == "EXIT":
            break

        ser.write((cmd + "\n").encode())

        # leitura não bloqueante
        time.sleep(0.05)
        while ser.in_waiting:
            resp = ser.readline().decode(errors="ignore").strip()
            if resp:
                print(f"[ARDUINO] {resp}")

except KeyboardInterrupt:
    pass

finally:
    ser.close()
    print("\n[INFO] Conexão encerrada")

import serial
import serial.tools.list_ports
import time
import sys

def detectar_arduino():
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        if "arduino" in desc or "cdc" in desc or "acm" in p.device.lower():
            return p.device
    return None

porta = detectar_arduino()

if not porta:
    print("Arduino não encontrado")
    sys.exit(1)

print(f"Arduino em {porta}")

ser = serial.Serial(porta, 9600, timeout=1)
time.sleep(2)

try:
    while True:
        cmd = input(">> ").strip().upper()

        if cmd == "EXIT":
            break

        ser.write((cmd + "\n").encode())
        resp = ser.readline().decode(errors="ignore").strip()

        if resp:
            print("Arduino:", resp)

except KeyboardInterrupt:
    pass

finally:
    ser.close()
    print("Conexão encerrada")

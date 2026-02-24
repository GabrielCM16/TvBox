import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

COR_JOGADOR = "0002550001"
COR_FIXO    = "2550000001"

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
        if "ACM" in p.device or "USB" in p.device:
            return p.device
    return None

porta = detectar_arduino() or "/dev/ttyACM0"
print("[PORTA]", porta)

ser = serial.Serial(
    porta,
    115200,
    timeout=1,
    write_timeout=1,
    rtscts=False,
    dsrdtr=False
)

# tempo real pro Arduino reiniciar
time.sleep(3)

# limpa qualquer lixo
ser.reset_input_buffer()

# espera READY (boot do Arduino)
print("[INFO] aguardando Arduino...")
t0 = time.time()
while time.time() - t0 < 5:
    line = ser.readline().decode(errors="ignore").strip()
    if line:
        print("[ARDUINO]", line)
        if "READY" in line:
            break

def enviar(cmd):
    ser.write((cmd+"\n").encode())
    ser.flush()

def apagar_led(l,c):
    enviar(f"{l}{c}")

def acender_led(l,c,cor):
    enviar(f"{l}{c}{cor}")

print("\n=== JOGO MATRIZ LED ===")
print("WASD mover | Q sair\n")

# inicialização confiável
enviar("CL")
acender_led(5,5,COR_FIXO)
acender_led(7,7,COR_FIXO)

linha = 0
coluna = 0
acender_led(linha,coluna,COR_JOGADOR)

def ler_retorno():
    while ser.in_waiting:
        print("[ARDUINO]", ser.readline().decode(errors="ignore").strip())

try:
    while True:
        cmd = getch().upper()

        if cmd == "Q":
            break

        nl, nc = linha, coluna
        if cmd=="W": nl-=1
        elif cmd=="S": nl+=1
        elif cmd=="A": nc-=1
        elif cmd=="D": nc+=1
        else: 
            continue

        if 0<=nl<MATRIZ_LINHAS and 0<=nc<MATRIZ_COLUNAS:
            apagar_led(linha,coluna)
            linha,coluna = nl,nc
            acender_led(linha,coluna,COR_JOGADOR)

        ler_retorno()

except KeyboardInterrupt:
    pass

finally:
    enviar("CL")
    ser.close()
    print("[INFO] encerrado")
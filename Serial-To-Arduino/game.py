import serial
import serial.tools.list_ports
import time
import sys
import tty
import termios
import random

MATRIZ_LINHAS = 8
MATRIZ_COLUNAS = 8

COR_JOGADOR     = "0002550001"
COR_MEMORIA     = "2550000001"
COR_SELECIONADO = "0000002551"
COR_DERROTA     = "2551280001"
COR_VITORIA     = "2552552551"

QTD_LEDS_MEMORIA = 2
MAX_ERROS = 3

USB_PACING = 0.003   # ESSENCIAL NA TV BOX

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
    return "/dev/ttyACM0"

porta = detectar_arduino()
print("[PORTA]", porta)

ser = serial.Serial(porta,115200,timeout=1,write_timeout=1,rtscts=False,dsrdtr=False)
time.sleep(3)

ser.reset_input_buffer()

# aguarda READY
t0=time.time()
while time.time()-t0<4:
    r=ser.readline().decode(errors="ignore").strip()
    if r:
        print("[ARDUINO]",r)
        if "READY" in r:
            break

# ---------- SERIAL SAFE ----------
def enviar(cmd):
    ser.write((cmd+"\n").encode())
    ser.flush()
    time.sleep(USB_PACING)

def apagar_led(l,c):
    enviar(f"{l}{c}")

def acender_led(l,c,cor):
    enviar(f"{l}{c}{cor}")

def limpar_matriz():
    enviar("CL")

# ---------- ANIMAÇÕES ----------
def preencher(cor):
    for l in range(MATRIZ_LINHAS):
        for c in range(MATRIZ_COLUNAS):
            acender_led(l,c,cor)

def animacao_derrota():
    for _ in range(2):
        preencher(COR_DERROTA)
        time.sleep(0.12)
        limpar_matriz()
        time.sleep(0.1)

def animacao_game_over():
    for _ in range(3):
        preencher(COR_DERROTA)
        time.sleep(0.25)
        limpar_matriz()
        time.sleep(0.2)

def animacao_vitoria():
    for _ in range(3):
        limpar_matriz()
        time.sleep(0.12)
        preencher(COR_VITORIA)
        time.sleep(0.18)
    limpar_matriz()

# ---------- JOGO ----------
print("\n=== JOGO MATRIZ LED ===")
print("WASD mover | ENTER marcar | P sair\n")

limpar_matriz()

posicoes=random.sample(range(64),QTD_LEDS_MEMORIA)
leds_memoria={(p//8,p%8) for p in posicoes}

acertos=set()
erros_totais=0
linha,coluna=0,0
jogo_iniciado=False

# mostra memória
for l,c in leds_memoria:
    acender_led(l,c,COR_MEMORIA)

acender_led(linha,coluna,COR_JOGADOR)

try:
    while True:
        cmd=getch().upper()

        if cmd in ("\r","\n"):
            cmd="ENTER"

        if cmd=="P":
            break

        # primeira ação do jogador apaga memória
        if not jogo_iniciado and cmd in ("W","A","S","D","ENTER"):
            limpar_matriz()
            acender_led(linha,coluna,COR_JOGADOR)
            jogo_iniciado=True

        # seleção
        if cmd=="ENTER":
            if (linha,coluna) in leds_memoria:
                if (linha,coluna) not in acertos:
                    acertos.add((linha,coluna))
                    acender_led(linha,coluna,COR_SELECIONADO)

                    if acertos==leds_memoria:
                        animacao_vitoria()
                        break
            else:
                erros_totais+=1
                animacao_derrota()

                if erros_totais>=MAX_ERROS:
                    print("GAME OVER")
                    animacao_game_over()
                    break

                print(f"Erro {erros_totais}/{MAX_ERROS}")
                acertos.clear()
                linha,coluna=0,0
                jogo_iniciado=False

                limpar_matriz()
                for l,c in leds_memoria:
                    acender_led(l,c,COR_MEMORIA)
                acender_led(linha,coluna,COR_JOGADOR)
            continue

        # movimento
        nl,nc=linha,coluna
        if cmd=="W": nl-=1
        elif cmd=="S": nl+=1
        elif cmd=="A": nc-=1
        elif cmd=="D": nc+=1
        else: continue

        if 0<=nl<8 and 0<=nc<8:
            if (linha,coluna) not in acertos:
                apagar_led(linha,coluna)
            else:
                acender_led(linha,coluna,COR_SELECIONADO)

            linha,coluna=nl,nc
            acender_led(linha,coluna,COR_JOGADOR)

except KeyboardInterrupt:
    pass

limpar_matriz()
ser.close()
print("[INFO] encerrado")
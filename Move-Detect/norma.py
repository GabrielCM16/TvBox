#!/usr/bin/env python3
from evdev import InputDevice, list_devices, ecodes
import math, time

# =========================
# TUNING (ajuste fino)
# =========================
DEADZONE = 3          # ignora tremedeira: |dx| e |dy| abaixo disso
WINDOW_MS = 60        # acumula movimento numa janelinha (ms)
SMOOTH = 0.35         # 0..1 (quanto maior, mais suave/lento)
MAX_MAG = 40.0        # magnitude que vira "100" no output (normalização)

def achar_mouse():
    best = None
    best_score = -1
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)
        tem_rel = ecodes.EV_REL in caps and any(
            c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)
        )
        if not tem_rel:
            continue
        tem_btn = ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]
        score = 2 if tem_btn else 1
        if score > best_score:
            best_score = score
            best = dev
    return best

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def main():
    dev = achar_mouse()
    if not dev:
        print("[ERRO] Nenhum dispositivo REL_X/REL_Y encontrado.")
        return

    print(f"[OK] {dev.path} | {dev.name}")
    print("Saída: DIREÇÃO + intensidade 0..100 (deadzone + smoothing). Ctrl+C para sair.\n")

    acc_dx = 0
    acc_dy = 0
    last_emit = time.monotonic()

    # para suavização (IIR)
    sm_dx = 0.0
    sm_dy = 0.0

    try:
        for e in dev.read_loop():
            if e.type == ecodes.EV_REL:
                if e.code == ecodes.REL_X:
                    acc_dx += e.value
                elif e.code == ecodes.REL_Y:
                    acc_dy += e.value

            now = time.monotonic()
            if (now - last_emit) * 1000.0 >= WINDOW_MS:
                # aplica deadzone por eixo
                dx = 0 if abs(acc_dx) < DEADZONE else acc_dx
                dy = 0 if abs(acc_dy) < DEADZONE else acc_dy

                # zera acumuladores da janela
                acc_dx = 0
                acc_dy = 0
                last_emit = now

                # suavização
                sm_dx = (1.0 - SMOOTH) * sm_dx + SMOOTH * dx
                sm_dy = (1.0 - SMOOTH) * sm_dy + SMOOTH * dy

                # se ainda está na deadzone, ignora
                if sm_dx == 0 and sm_dy == 0:
                    continue

                # escolhe direção dominante (4 direções)
                if abs(sm_dx) >= abs(sm_dy):
                    direcao = "RIGHT" if sm_dx > 0 else "LEFT"
                    mag = abs(sm_dx)
                else:
                    # em mouse, dy positivo normalmente = desceu
                    direcao = "DOWN" if sm_dy > 0 else "UP"
                    mag = abs(sm_dy)

                # normaliza para 0..100 com curva mais “bonita”
                # (raiz dá mais sensibilidade em movimentos pequenos)
                mag_n = clamp(mag / MAX_MAG, 0.0, 1.0)
                bonito = int(round(100.0 * math.sqrt(mag_n)))

                if bonito > 0:
                    print(f"{direcao:<5} {bonito:3d}")

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

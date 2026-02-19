#!/usr/bin/env python3
import time, select
from evdev import InputDevice, list_devices, ecodes

# ====== Ajustes principais ======
DEADZONE = 1
WINDOW_MS = 30
SMOOTH = 0.55

# Gatilho no bruto (robusto)
MIN_SM_UP = 6.0          # intensidade mínima (subir)
DELTA_SM_TRIGGER = 6.0   # salto mínimo

# Anti "flap em cima do outro"
MIN_GAP_S = 0.30         # mínimo entre flaps (0,30s)
REARM_LEVEL = 2.5        # precisa cair abaixo disso para rearmar (histerese)

# Se seu eixo for o inverso, troque USE_UP_SIGN
# "UP" = dy negativo (comum em mouse). Se no seu for ao contrário, coloque False.
USE_UP_SIGN = True


def achar_mouse():
    candidatos = []
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)

        tem_rel = ecodes.EV_REL in caps and any(
            c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)
        )
        tem_btn = ecodes.EV_KEY in caps and ecodes.BTN_LEFT in caps[ecodes.EV_KEY]

        if tem_rel:
            candidatos.append((2 if tem_btn else 1, dev))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[0], reverse=True)
    return candidatos[0][1]


def main():
    dev = achar_mouse()
    if not dev:
        print("[ERRO] Nenhum dispositivo com REL_X/REL_Y encontrado.")
        return

    print(f"[OK] {dev.path} | {dev.name}")
    print("Rodando... (só imprime quando houver FLAP)  Ctrl+C para sair.\n")

    acc_dx = acc_dy = 0
    sm_dx = sm_dy = 0.0
    last_emit = time.monotonic()

    last_flap_t = -1e9
    armed = True

    prev_up = 0.0

    try:
        while True:
            # drena eventos disponíveis
            while True:
                r, _, _ = select.select([dev.fd], [], [], 0)
                if not r:
                    break
                e = dev.read_one()
                if e is None:
                    break
                if e.type == ecodes.EV_REL:
                    if e.code == ecodes.REL_X:
                        acc_dx += e.value
                    elif e.code == ecodes.REL_Y:
                        acc_dy += e.value

            now = time.monotonic()
            if (now - last_emit) * 1000.0 < WINDOW_MS:
                time.sleep(0.002)
                continue
            last_emit = now

            dx = 0 if abs(acc_dx) < DEADZONE else acc_dx
            dy = 0 if abs(acc_dy) < DEADZONE else acc_dy
            acc_dx = acc_dy = 0

            # suavização
            sm_dx = (1.0 - SMOOTH) * sm_dx + SMOOTH * dx
            sm_dy = (1.0 - SMOOTH) * sm_dy + SMOOTH * dy

            # componente "UP"
            if USE_UP_SIGN:
                up = max(0.0, -sm_dy)   # só considera subir (dy negativo)
            else:
                up = max(0.0, sm_dy)    # se seu dispositivo for invertido

            delta_up = up - prev_up
            prev_up = up

            # rearme por histerese: só volta a armar quando a intensidade cai
            if not armed and up <= REARM_LEVEL:
                armed = True

            # regras de disparo
            gap_ok = (now - last_flap_t) >= MIN_GAP_S
            intensity_ok = up >= MIN_SM_UP
            delta_ok = delta_up >= DELTA_SM_TRIGGER

            if armed and gap_ok and intensity_ok and delta_ok:
                last_flap_t = now
                armed = False
                print(f"[FLAP] t={now:0.3f}s  up={up:0.2f}  delta={delta_up:0.2f}")

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

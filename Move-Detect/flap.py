#!/usr/bin/env python3
import time, math, select
from evdev import InputDevice, list_devices, ecodes

DEADZONE = 1          # antes 3
WINDOW_MS = 30        # antes 55 (mais responsivo)
SMOOTH = 0.55         # antes 0.20 (menos “amarrado”)
COOLDOWN_MS = 180

# gatilhos no "mundo real" (bruto), não no 0..100
MIN_SM_DY = 6.0       # intensidade mínima (ajuste fino)
DELTA_SM_TRIGGER = 6.0 # salto mínimo (ajuste fino)

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
        print("[ERRO] sem REL_X/REL_Y")
        return

    print(f"[OK] {dev.path} | {dev.name}")

    acc_dx = acc_dy = 0
    sm_dx = sm_dy = 0.0
    last_emit = time.monotonic()
    last_fire = 0.0
    prev_sm_abs_dy = 0.0

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
                if e.code == ecodes.REL_X: acc_dx += e.value
                elif e.code == ecodes.REL_Y: acc_dy += e.value

        now = time.monotonic()
        if (now - last_emit) * 1000.0 < WINDOW_MS:
            time.sleep(0.002)
            continue
        last_emit = now

        dx = 0 if abs(acc_dx) < DEADZONE else acc_dx
        dy = 0 if abs(acc_dy) < DEADZONE else acc_dy
        acc_dx = acc_dy = 0

        sm_dx = (1.0 - SMOOTH) * sm_dx + SMOOTH * dx
        sm_dy = (1.0 - SMOOTH) * sm_dy + SMOOTH * dy

        sm_abs_dy = abs(sm_dy)
        delta_sm = sm_abs_dy - prev_sm_abs_dy
        prev_sm_abs_dy = sm_abs_dy

        flap = False
        if sm_abs_dy >= MIN_SM_DY and delta_sm >= DELTA_SM_TRIGGER:
            if (now - last_fire) * 1000.0 >= COOLDOWN_MS:
                last_fire = now
                flap = True

        print(
            f"raw(dx,dy)=({dx:+4},{dy:+4})  "
            f"sm(dx,dy)=({sm_dx:+6.2f},{sm_dy:+6.2f})  "
            f"|sm_dy|={sm_abs_dy:6.2f}  d={delta_sm:6.2f}  "
            f"{'FLAP!' if flap else ''}"
        )

if __name__ == "__main__":
    main()

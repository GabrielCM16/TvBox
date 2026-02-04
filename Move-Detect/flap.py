#!/usr/bin/env python3
import time, math, select
from evdev import InputDevice, list_devices, ecodes

DEADZONE = 3
WINDOW_MS = 55
SMOOTH = 0.20
MAX_MAG = 40.0

MIN_INT = 20          # precisa estar pelo menos nisso
DELTA_TRIGGER = 18    # salto mínimo pra considerar "flap"
COOLDOWN_MS = 180

def achar_mouse():
    best = None
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities(verbose=False)
        if ecodes.EV_REL in caps and any(c in caps[ecodes.EV_REL] for c in (ecodes.REL_X, ecodes.REL_Y)):
            best = dev
    return best

def norm_0_100(mag):
    mag_n = max(0.0, min(1.0, mag / MAX_MAG))
    return int(round(100.0 * math.sqrt(mag_n)))

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
    prev_vert = 0

    while True:
        # drain
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
            time.sleep(0.005)
            continue
        last_emit = now

        dx = 0 if abs(acc_dx) < DEADZONE else acc_dx
        dy = 0 if abs(acc_dy) < DEADZONE else acc_dy
        acc_dx = acc_dy = 0

        sm_dx = (1.0 - SMOOTH) * sm_dx + SMOOTH * dx
        sm_dy = (1.0 - SMOOTH) * sm_dy + SMOOTH * dy

        vert = norm_0_100(abs(sm_dy))
        anyi = norm_0_100(math.hypot(sm_dx, sm_dy))

        delta = vert - prev_vert
        prev_vert = vert

        flap = False
        if vert >= MIN_INT and delta >= DELTA_TRIGGER:
            if (now - last_fire) * 1000.0 >= COOLDOWN_MS:
                last_fire = now
                flap = True

        print(f"any={anyi:3d} vert={vert:3d} delta={delta:4d}  {'FLAP!' if flap else ''}")

if __name__ == "__main__":
    main()
